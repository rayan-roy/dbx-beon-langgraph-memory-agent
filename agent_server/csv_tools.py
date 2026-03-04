"""LangGraph tools for querying uploaded CSV data.

Follows the factory function pattern from memory_tools.py.
Tools access thread_id from RunnableConfig to scope queries to the current session.
"""

import logging
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.store.base import BaseStore

from agent_server.csv_store import (
    META_KEY_PREFIX,
    CSV_NAMESPACE_PREFIX,
)

logger = logging.getLogger(__name__)


def csv_tools():
    """Factory function returning CSV query tools for the agent.

    Returns a list of tools:
    - search_uploaded_csv: Semantic search over CSV data for the current thread.
    - describe_uploaded_csvs: Returns metadata about uploaded CSVs.

    Usage:
        tools = await mcp_client.get_tools() + csv_tools()
        config = {"configurable": {"thread_id": thread_id, "store": store}}
    """

    @tool
    async def search_uploaded_csv(query: str, config: RunnableConfig) -> str:
        """Search the uploaded CSV data for relevant rows matching the query.

        Use this when the user asks questions about data they uploaded via CSV.
        Returns matching rows with their values.

        Args:
            query: Natural language description of what to search for in the CSV data.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return "CSV search not available - no thread_id provided."

        store: Optional[BaseStore] = config.get("configurable", {}).get("store")
        if not store:
            return "CSV search not available - store not configured."

        namespace = (CSV_NAMESPACE_PREFIX, thread_id)
        results = await store.asearch(namespace, query=query, limit=10)

        # Filter out metadata entries
        data_results = [r for r in results if not r.key.startswith(META_KEY_PREFIX)]

        if not data_results:
            return "No matching CSV data found. The user may not have uploaded a CSV yet."

        rows = []
        for item in data_results:
            text = item.value.get("text", "")
            rows.append(f"- {text}")

        return f"Found {len(data_results)} matching rows:\n" + "\n".join(rows)

    @tool
    async def describe_uploaded_csvs(config: RunnableConfig) -> str:
        """Describe the CSV files that have been uploaded in this session.

        Use this to understand what data is available before querying it.
        Returns filenames, column names, and row counts.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return "CSV info not available - no thread_id provided."

        store: Optional[BaseStore] = config.get("configurable", {}).get("store")
        if not store:
            return "CSV info not available - store not configured."

        namespace = (CSV_NAMESPACE_PREFIX, thread_id)
        results = await store.asearch(namespace, query="csv file metadata", limit=100)

        meta_results = [r for r in results if r.key.startswith(META_KEY_PREFIX)]

        if not meta_results:
            return "No CSV files have been uploaded in this session."

        descriptions = []
        for item in meta_results:
            v = item.value
            filename = v.get("filename", "unknown")
            columns = v.get("columns", [])
            row_count = v.get("row_count", 0)
            descriptions.append(
                f"- **{filename}**: {row_count} rows, columns: {', '.join(columns)}"
            )

        return f"Uploaded CSV files:\n" + "\n".join(descriptions)

    return [search_uploaded_csv, describe_uploaded_csvs]
