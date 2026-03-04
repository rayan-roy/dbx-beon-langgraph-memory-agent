"""CSV ingestion and storage module using AsyncDatabricksStore with pgvector.

Stores CSV rows as embeddings scoped to a thread_id namespace, enabling
semantic search over uploaded CSV data within a chat session.
"""

import csv
import io
import logging
import os
from typing import Any

from databricks_langchain import AsyncDatabricksStore

from agent_server.utils import ensure_lakebase_instance

logger = logging.getLogger(__name__)

LAKEBASE_INSTANCE_NAME = ensure_lakebase_instance(os.getenv("LAKEBASE_INSTANCE_NAME", ""))
EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1024"))

CSV_NAMESPACE_PREFIX = "csv_data"
META_KEY_PREFIX = "_meta_"


def _get_store() -> AsyncDatabricksStore:
    return AsyncDatabricksStore(
        instance_name=LAKEBASE_INSTANCE_NAME,
        embedding_endpoint=EMBEDDING_ENDPOINT,
        embedding_dims=EMBEDDING_DIMS,
    )


def _row_to_text(row: dict[str, str]) -> str:
    """Convert a CSV row dict to a pipe-delimited text string for embedding."""
    return " | ".join(f"{k}: {v}" for k, v in row.items() if v)


async def ingest_csv(
    thread_id: str, csv_content: str, filename: str
) -> dict[str, Any]:
    """Parse CSV and store each row in AsyncDatabricksStore scoped to thread_id.

    Args:
        thread_id: The chat session ID to scope data to.
        csv_content: Raw CSV text content.
        filename: Original filename for metadata.

    Returns:
        Dict with filename, columns, row_count, and thread_id.
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    columns = reader.fieldnames or []
    if not columns:
        raise ValueError("CSV file has no columns/headers.")

    namespace = (CSV_NAMESPACE_PREFIX, thread_id)

    logger.info(f"Starting CSV ingestion: file='{filename}', thread='{thread_id}', columns={columns}")

    async with _get_store() as store:
        await store.setup()
        logger.info(f"Lakebase store setup complete for instance '{LAKEBASE_INSTANCE_NAME}'")

        rows_stored = 0
        for i, row in enumerate(reader):
            text = _row_to_text(row)
            key = f"row_{filename}_{i}"
            await store.aput(
                namespace,
                key,
                {"text": text, "row_index": i, "filename": filename, **row},
            )
            rows_stored += 1

        # Store metadata entry for this file
        meta_key = f"{META_KEY_PREFIX}{filename}"
        await store.aput(
            namespace,
            meta_key,
            {
                "filename": filename,
                "columns": columns,
                "row_count": rows_stored,
            },
        )

    logger.info(
        f"CSV ingestion complete: {rows_stored} rows from '{filename}' stored in Lakebase namespace=('csv_data', '{thread_id}')"
    )
    return {
        "filename": filename,
        "columns": columns,
        "row_count": rows_stored,
        "thread_id": thread_id,
    }


async def search_csv_data(
    thread_id: str, query: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Semantic search over stored CSV rows for a given thread.

    Args:
        thread_id: The chat session ID.
        query: Natural language search query.
        limit: Max number of results to return.

    Returns:
        List of matching row dicts with scores.
    """
    namespace = (CSV_NAMESPACE_PREFIX, thread_id)

    async with _get_store() as store:
        results = await store.asearch(namespace, query=query, limit=limit)

    return [
        {"key": item.key, "score": getattr(item, "score", None), **item.value}
        for item in results
        if not item.key.startswith(META_KEY_PREFIX)
    ]


async def get_csv_metadata(thread_id: str) -> list[dict[str, Any]]:
    """Return metadata about uploaded CSVs in a thread.

    Args:
        thread_id: The chat session ID.

    Returns:
        List of metadata dicts with filename, columns, row_count.
    """
    namespace = (CSV_NAMESPACE_PREFIX, thread_id)

    async with _get_store() as store:
        # Search for metadata entries using a broad query
        results = await store.asearch(namespace, query="csv file metadata", limit=100)

    return [
        item.value
        for item in results
        if item.key.startswith(META_KEY_PREFIX)
    ]


async def delete_csv_data(thread_id: str) -> int:
    """Delete all CSV data for a thread (session cleanup).

    Args:
        thread_id: The chat session ID.

    Returns:
        Number of items deleted.
    """
    namespace = (CSV_NAMESPACE_PREFIX, thread_id)

    async with _get_store() as store:
        # List all items in the namespace
        results = await store.asearch(namespace, query="", limit=10000)
        count = 0
        for item in results:
            await store.adelete(namespace, item.key)
            count += 1

    logger.info(f"Deleted {count} CSV items for thread '{thread_id}'")
    return count
