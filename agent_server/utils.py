import logging
from typing import Any, AsyncGenerator, AsyncIterator, Optional

from databricks.sdk import WorkspaceClient
from databricks_langchain.chat_models import json
from langchain.messages import AIMessageChunk, ToolMessage
from mlflow.genai.agent_server import get_request_headers
from mlflow.types.responses import (
    ResponsesAgentStreamEvent,
    create_text_delta,
    output_to_responses_items_stream,
)


def get_user_workspace_client() -> WorkspaceClient:
    token = get_request_headers().get("x-forwarded-access-token")
    return WorkspaceClient(token=token, auth_type="pat")


def resolve_lakebase_instance_name(
    instance_name: str, workspace_client: Optional[WorkspaceClient] = None
) -> str:
    """Resolve a Lakebase instance name from a hostname if needed.

    When using valueFrom in app.yaml, Databricks Apps resolves the database
    resource to a hostname rather than the instance name. This function
    detects that and resolves it back to the instance name.
    """
    if not (".database." in instance_name and instance_name.endswith(".com")):
        return instance_name

    client = workspace_client or WorkspaceClient()
    hostname = instance_name

    try:
        instances = list(client.database.list_database_instances())
    except Exception as exc:
        raise ValueError(
            f"Unable to list database instances to resolve hostname '{hostname}'."
        ) from exc

    for instance in instances:
        rw_dns = getattr(instance, "read_write_dns", None)
        ro_dns = getattr(instance, "read_only_dns", None)
        if hostname in (rw_dns, ro_dns):
            resolved_name = getattr(instance, "name", None)
            if resolved_name:
                logging.info(f"Resolved Lakebase hostname '{hostname}' to '{resolved_name}'")
                return resolved_name

    raise ValueError(
        f"Unable to resolve Lakebase instance '{hostname}'. "
        "Ensure the instance name is correct."
    )


DEFAULT_LAKEBASE_INSTANCE_NAME = "agent-langgraph-memory-lb"


def ensure_lakebase_instance(
    instance_name: str = "",
    workspace_client: Optional[WorkspaceClient] = None,
) -> str:
    """Ensure a Lakebase instance exists, creating one if needed.

    If instance_name is provided, resolves it (hostname → name if needed).
    If instance_name is empty, looks for an existing instance or creates a new one.

    Returns the resolved instance name.
    """
    client = workspace_client or WorkspaceClient()

    # If a name was provided, just resolve and return it
    if instance_name:
        return resolve_lakebase_instance_name(instance_name, client)

    # No name provided — check for existing instances
    try:
        instances = list(client.database.list_database_instances())
    except Exception:
        instances = []

    # First, check if our default-named instance already exists
    for inst in instances:
        name = getattr(inst, "name", None)
        if name == DEFAULT_LAKEBASE_INSTANCE_NAME:
            state = getattr(inst, "state", None)
            logging.info(f"Found our Lakebase instance '{name}' (state: {state})")
            return name

    # Next, look for any instance created by the current SP (app identity)
    try:
        current_sp = client.current_user.me().user_name
    except Exception:
        current_sp = None
    if current_sp:
        for inst in instances:
            creator = getattr(inst, "creator", None)
            name = getattr(inst, "name", None)
            if name and creator == current_sp:
                logging.info(f"Found Lakebase instance created by this app: {name}")
                return name

    # No running instance found — create one
    logging.info(f"No Lakebase instance found. Creating '{DEFAULT_LAKEBASE_INSTANCE_NAME}'...")
    from databricks.sdk.service.database import DatabaseInstance

    try:
        waiter = client.database.create_database_instance(
            DatabaseInstance(name=DEFAULT_LAKEBASE_INSTANCE_NAME, capacity="CU_1")
        )
        result = waiter.result()
        name = getattr(result, "name", DEFAULT_LAKEBASE_INSTANCE_NAME)
        logging.info(f"Created Lakebase instance: {name}")
        return name
    except Exception as exc:
        error_msg = str(exc).lower()
        # If instance already exists (race condition or previous run), use it
        if "already exists" in error_msg or "not unique" in error_msg:
            logging.info(f"Instance '{DEFAULT_LAKEBASE_INSTANCE_NAME}' already exists, using it.")
            return DEFAULT_LAKEBASE_INSTANCE_NAME
        raise ValueError(
            f"Failed to create Lakebase instance '{DEFAULT_LAKEBASE_INSTANCE_NAME}': {exc}"
        ) from exc


def get_databricks_host_from_env() -> Optional[str]:
    try:
        w = WorkspaceClient()
        return w.config.host
    except Exception as e:
        logging.exception(f"Error getting databricks host from env: {e}")
        return None


async def process_agent_astream_events(
    async_stream: AsyncIterator[Any],
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    """
    Generic helper to process agent stream events and yield ResponsesAgentStreamEvent objects.

    Args:
        async_stream: The async iterator from agent.astream()
    """
    async for event in async_stream:
        if event[0] == "updates":
            for node_data in event[1].values():
                if len(node_data.get("messages", [])) > 0:
                    for msg in node_data["messages"]:
                        if isinstance(msg, ToolMessage) and not isinstance(msg.content, str):
                            msg.content = json.dumps(msg.content)
                    for item in output_to_responses_items_stream(node_data["messages"]):
                        yield item
        elif event[0] == "messages":
            try:
                chunk = event[1][0]
                if isinstance(chunk, AIMessageChunk) and (content := chunk.content):
                    yield ResponsesAgentStreamEvent(
                        **create_text_delta(delta=content, item_id=chunk.id)
                    )
            except Exception as e:
                logging.exception(f"Error processing agent stream event: {e}")
