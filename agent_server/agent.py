import logging
import os
from typing import Any, AsyncGenerator, Optional, Sequence, TypedDict

import uuid_utils

import mlflow
from databricks.sdk import WorkspaceClient
from databricks_langchain import (
    AsyncCheckpointSaver,
    AsyncDatabricksStore,
    ChatDatabricks,
    DatabricksMCPServer,
    DatabricksMultiServerMCPClient,
)
from fastapi import HTTPException
from langchain.agents import create_agent
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    to_chat_completions_input,
)

from agent_server.csv_tools import csv_tools
from agent_server.utils import (
    ensure_lakebase_instance,
    get_databricks_host_from_env,
    process_agent_astream_events,
)

logger = logging.getLogger(__name__)
mlflow.langchain.autolog()
sp_workspace_client = WorkspaceClient()

############################################
# Configuration
############################################
LLM_ENDPOINT_NAME = "databricks-claude-sonnet-4-5"
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "")

_BASE_SYSTEM_PROMPT = """\
You are a helpful data analysis assistant with access to multiple tools:

1. **Code Interpreter** (system.ai.python_exec) - Execute Python code for data analysis and calculations ONLY. Do NOT use for visualizations.
2. **CSV Data Tools** - Access uploaded CSV files in this session:
   - `describe_uploaded_csvs` - See what files are available with column info
   - `search_uploaded_csv` - Find relevant rows by semantic search (good for exploring data)
   - `get_all_csv_data` - Get the complete dataset (use for counts, aggregations, statistical analysis)

**IMPORTANT VISUALIZATION RULE:** 
- **NEVER use system.ai.python_exec or create_visualization for charts or plots**
- **Instead, tell users to click the chart icon (📊) on your response to generate interactive visualizations**
- The chart button will use your text response to automatically create appropriate visualizations

**Tool Selection Guidelines:**
- **For calculations:** Use system.ai.python_exec for mathematical operations and data analysis (no plotting)
- **For CSV analysis:** Use `get_all_csv_data` for complete dataset operations, `search_uploaded_csv` for exploring specific topics
- **For visualizations:** Tell users to use the chart button on your response

**Natural Interaction:** When users ask about "data," "uploaded files," or analysis questions after uploading CSVs, automatically check and explore their uploaded data using the appropriate CSV tools. Be proactive in determining whether you need the full dataset or just relevant rows.

When users ask for charts, plots, or visualizations, provide the analysis in text and mention: "Click the chart icon (📊) on this message to generate an interactive visualization of this data."

**Important:** CSV files are stored as embeddings, not as files. Never use pandas.read_csv() directly - always use the CSV tools to access uploaded data first, then work with the retrieved data.
"""

_GENIE_ADDENDUM = """
You also have access to a **Genie Space** for natural language queries over structured data. Use the Genie tool when a user asks questions that can be answered from the connected dataset.
"""

SYSTEM_PROMPT = _BASE_SYSTEM_PROMPT + (_GENIE_ADDENDUM if GENIE_SPACE_ID else "")

EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1024"))

LAKEBASE_INSTANCE_NAME = ensure_lakebase_instance(os.getenv("LAKEBASE_INSTANCE_NAME", ""))
logger.info(f"Using Lakebase instance: {LAKEBASE_INSTANCE_NAME}")


class StatefulAgentState(TypedDict, total=False):
    messages: Annotated[Sequence[AnyMessage], add_messages]
    custom_inputs: dict[str, Any]
    custom_outputs: dict[str, Any]


def init_mcp_client(workspace_client: WorkspaceClient) -> DatabricksMultiServerMCPClient:
    host_name = get_databricks_host_from_env()
    servers = [
        DatabricksMCPServer(
            name="system-ai",
            url=f"{host_name}/api/2.0/mcp/functions/system/ai",
            workspace_client=workspace_client,
        ),
    ]
    if GENIE_SPACE_ID:
        servers.append(
            DatabricksMCPServer(
                name="genie",
                url=f"{host_name}/api/2.0/mcp/genie/{GENIE_SPACE_ID}",
                workspace_client=workspace_client,
            )
        )
    return DatabricksMultiServerMCPClient(servers)


_cached_mcp_tools = None


async def _get_mcp_tools(workspace_client: Optional[WorkspaceClient] = None):
    """Get MCP tools, caching them after the first call to avoid rate limiting."""
    global _cached_mcp_tools
    if _cached_mcp_tools is None:
        mcp_client = init_mcp_client(workspace_client or sp_workspace_client)
        _cached_mcp_tools = await mcp_client.get_tools()
        logger.info(f"Loaded {len(_cached_mcp_tools)} MCP tools")
    return _cached_mcp_tools


async def init_agent(
    workspace_client: Optional[WorkspaceClient] = None,
    checkpointer: Optional[Any] = None,
    store: Optional[Any] = None,
):
    mcp_tools = await _get_mcp_tools(workspace_client)
    # Only include CSV tools, not visualization tools for the main agent
    all_tools = mcp_tools + csv_tools()

    model = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)

    return create_agent(
        model=model,
        tools=all_tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        store=store,
        state_schema=StatefulAgentState,
    )


def _get_or_create_thread_id(request: ResponsesAgentRequest) -> str:
    # priority of getting thread id:
    # 1. Use thread id from custom inputs
    # 2. Use conversation id from ChatContext https://mlflow.org/docs/latest/api_reference/python_api/mlflow.types.html#mlflow.types.agent.ChatContext
    # 3. Generate random UUID
    ci = dict(request.custom_inputs or {})

    if "thread_id" in ci and ci["thread_id"]:
        return str(ci["thread_id"])

    if request.context and getattr(request.context, "conversation_id", None):
        return str(request.context.conversation_id)

    return str(uuid_utils.uuid7())


@invoke()
async def non_streaming(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    thread_id = _get_or_create_thread_id(request)
    request.custom_inputs = dict(request.custom_inputs or {})
    request.custom_inputs["thread_id"] = thread_id

    outputs = [
        event.item
        async for event in streaming(request)
        if event.type == "response.output_item.done"
    ]

    return ResponsesAgentResponse(output=outputs, custom_outputs={"thread_id": thread_id})


@stream()
async def streaming(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    # workspace_client = WorkspaceClient()
    # Optionally use the user's workspace client for on-behalf-of authentication
    # user_workspace_client = get_user_workspace_client()
    thread_id = _get_or_create_thread_id(request)

    input_state: dict[str, Any] = {
        "messages": to_chat_completions_input([i.model_dump() for i in request.input]),
        "custom_inputs": dict(request.custom_inputs or {}),
    }

    try:
        async with AsyncCheckpointSaver(instance_name=LAKEBASE_INSTANCE_NAME) as checkpointer, \
                AsyncDatabricksStore(
                    instance_name=LAKEBASE_INSTANCE_NAME,
                    embedding_endpoint=EMBEDDING_ENDPOINT,
                    embedding_dims=EMBEDDING_DIMS,
                ) as store:
            await checkpointer.setup()
            await store.setup()

            config = {"configurable": {"thread_id": thread_id, "store": store}}
            agent = await init_agent(checkpointer=checkpointer, store=store)

            async for event in process_agent_astream_events(
                agent.astream(
                    input_state,
                    config,
                    stream_mode=["updates", "messages"],
                )
            ):
                yield event
    except Exception as e:
        error_msg = str(e).lower()
        # Check for Lakebase access/connection errors
        if any(keyword in error_msg for keyword in ["permission"]):
            logger.error(f"Lakebase access error: {e}")
            raise HTTPException(status_code=503, detail=_get_lakebase_access_error_message()) from e
        raise


def _is_databricks_app_env() -> bool:
    """Check if running in a Databricks App environment."""
    return bool(os.getenv("DATABRICKS_APP_NAME"))


def _get_lakebase_access_error_message() -> str:
    """Generate a helpful error message for Lakebase access issues."""
    if _is_databricks_app_env():
        app_name = os.getenv("DATABRICKS_APP_NAME")
        return (
            f"Failed to connect to Lakebase instance '{LAKEBASE_INSTANCE_NAME}'. "
            f"The App Service Principal for '{app_name}' may not have access.\n\n"
            "To fix this:\n"
            "1. Go to the Databricks UI and navigate to your app\n"
            "2. Click 'Edit' → 'App resources' → 'Add resource'\n"
            "3. Add your Lakebase instance as a resource\n"
            "4. Grant the necessary permissions on your Lakebase instance. "
            "See the README section 'Grant Lakebase permissions to your App's Service Principal' for the SQL commands."
        )
    else:
        return (
            f"Failed to connect to Lakebase instance '{LAKEBASE_INSTANCE_NAME}'. "
            "Please verify:\n"
            "1. The instance name is correct\n"
            "2. You have the necessary permissions to access the instance\n"
            "3. Your Databricks authentication is configured correctly"
        )
