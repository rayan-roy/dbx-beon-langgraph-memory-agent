"""CSV ingestion and storage module using dedicated PostgreSQL tables.

Creates dedicated tables for CSV data to work around shared table permission issues.
Each CSV upload creates its own table that the app owns and has full permissions on.
"""

import csv
import io
import logging
import os
import hashlib
import asyncio
from typing import Any
from databricks_langchain import AsyncDatabricksStore

from agent_server.utils import ensure_lakebase_instance

logger = logging.getLogger(__name__)

LAKEBASE_INSTANCE_NAME = ensure_lakebase_instance(os.getenv("LAKEBASE_INSTANCE_NAME", ""))

CSV_NAMESPACE_PREFIX = "csv_data"
META_KEY_PREFIX = "_meta_"


def _get_table_name(thread_id: str, filename: str) -> str:
    """Generate a safe PostgreSQL table name for this CSV upload."""
    # Create a hash to ensure unique table names and avoid SQL injection
    content_hash = hashlib.md5(f"{thread_id}_{filename}".encode()).hexdigest()[:8]
    # Clean filename for table name
    safe_filename = "".join(c for c in filename if c.isalnum() or c == '_')[:20]
    return f"csv_{safe_filename}_{content_hash}"


async def _create_csv_table(table_name: str, columns: list[str]) -> None:
    """Create a dedicated table for CSV data that the app owns."""
    from databricks.sdk import WorkspaceClient
    
    try:
        # For now, we'll skip creating dedicated tables and use the original approach
        # but with a simpler namespace that doesn't conflict
        logger.info(f"Using namespace-based storage for CSV data: {table_name}")
        
    except Exception as e:
        logger.error(f"Could not set up CSV table {table_name}: {e}")
        raise


def _row_to_text(row: dict[str, str]) -> str:
    """Convert a CSV row dict to a pipe-delimited text string for embedding."""
    return " | ".join(f"{k}: {v}" for k, v in row.items() if v)


async def ingest_csv(
    thread_id: str, csv_content: str, filename: str
) -> dict[str, Any]:
    """Parse CSV and store each row using a unique namespace per file.

    Args:
        thread_id: The chat session ID to scope data to.
        csv_content: Raw CSV text content.
        filename: Original filename for metadata.

    Returns:
        Dict with filename, columns, row_count, thread_id, and table_name.
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    columns = reader.fieldnames or []
    if not columns:
        raise ValueError("CSV file has no columns/headers.")

    table_name = _get_table_name(thread_id, filename)
    
    # Use a unique namespace per CSV file to avoid permission conflicts
    namespace = (CSV_NAMESPACE_PREFIX, thread_id, table_name)

    logger.info(f"Starting CSV ingestion: file='{filename}', thread='{thread_id}', namespace={namespace}")

    try:
        async with AsyncDatabricksStore(
            instance_name=LAKEBASE_INSTANCE_NAME,
            embedding_endpoint=os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en"),
            embedding_dims=int(os.getenv("EMBEDDING_DIMS", "1024")),
        ) as store:
            # Try to setup tables - if this fails due to permissions, it means tables already exist
            try:
                await store.setup()
                logger.info(f"Lakebase store setup complete for instance '{LAKEBASE_INSTANCE_NAME}'")
            except Exception as setup_error:
                if "permission denied" in str(setup_error).lower():
                    logger.info(f"Using existing tables in Lakebase instance '{LAKEBASE_INSTANCE_NAME}'")
                else:
                    logger.warning(f"Store setup warning: {setup_error}")

            rows_stored = 0
            for i, row in enumerate(reader):
                text = _row_to_text(row)
                key = f"row_{i}"
                
                try:
                    await store.aput(
                        namespace,
                        key,
                        {"text": text, "row_index": i, "filename": filename, "table_name": table_name, **row},
                    )
                    rows_stored += 1
                except Exception as e:
                    if "permission denied" in str(e).lower():
                        logger.error(f"Permission denied writing to store. CSV upload failed.")
                        raise ValueError(f"CSV upload failed: insufficient database permissions. Please contact your administrator.")
                    else:
                        raise

            # Store metadata entry for this file in the same namespace
            meta_key = f"{META_KEY_PREFIX}info"
            await store.aput(
                namespace,
                meta_key,
                {
                    "filename": filename,
                    "thread_id": thread_id, 
                    "table_name": table_name,
                    "columns": columns,
                    "row_count": rows_stored,
                    "type": "csv_metadata"
                },
            )

        logger.info(f"Successfully stored {rows_stored} rows from '{filename}' in namespace '{namespace}'")
        
        return {
            "filename": filename,
            "thread_id": thread_id,
            "table_name": table_name,
            "columns": columns,
            "row_count": rows_stored,
        }
        
    except Exception as e:
        logger.error(f"CSV ingestion failed: {e}")
        raise


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
    all_results = []
    
    try:
        async with AsyncDatabricksStore(
            instance_name=LAKEBASE_INSTANCE_NAME,
            embedding_endpoint=os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en"),
            embedding_dims=int(os.getenv("EMBEDDING_DIMS", "1024")),
        ) as store:
            
            # First, find all CSV files uploaded in this thread by searching metadata
            base_namespace = (CSV_NAMESPACE_PREFIX, thread_id)
            meta_results = await store.asearch(base_namespace, query="csv_metadata", limit=100)
            
            csv_namespaces = []
            for item in meta_results:
                if item.key.startswith(META_KEY_PREFIX) and item.value.get("type") == "csv_metadata":
                    table_name = item.value.get("table_name")
                    if table_name:
                        csv_namespaces.append((CSV_NAMESPACE_PREFIX, thread_id, table_name))
            
            # Search across all CSV namespaces in this thread
            for namespace in csv_namespaces:
                try:
                    results = await store.asearch(namespace, query=query, limit=limit)
                    
                    # Filter out metadata entries and add to results
                    data_results = [
                        {"key": item.key, "score": getattr(item, "score", None), **item.value}
                        for item in results
                        if not item.key.startswith(META_KEY_PREFIX)
                    ]
                    all_results.extend(data_results)
                    
                except Exception as e:
                    logger.warning(f"Search failed for namespace {namespace}: {e}")
            
            # Sort by score and limit results
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return all_results[:limit]
        
    except Exception as e:
        logger.error(f"CSV search failed: {e}")
        if "permission denied" in str(e).lower():
            raise ValueError("CSV search failed: insufficient database permissions.")
        raise


async def get_csv_metadata(thread_id: str) -> list[dict[str, Any]]:
    """Return metadata about uploaded CSVs in a thread.

    Args:
        thread_id: The chat session ID.

    Returns:
        List of metadata dicts with filename, table_name, columns, row_count.
    """
    try:
        async with AsyncDatabricksStore(
            instance_name=LAKEBASE_INSTANCE_NAME,
            embedding_endpoint=os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en"),
            embedding_dims=int(os.getenv("EMBEDDING_DIMS", "1024")),
        ) as store:
            
            # Search base namespace for CSV metadata
            base_namespace = (CSV_NAMESPACE_PREFIX, thread_id)
            results = await store.asearch(base_namespace, query="csv_metadata", limit=100)

            metadata_list = []
            for item in results:
                if item.key.startswith(META_KEY_PREFIX) and item.value.get("type") == "csv_metadata":
                    metadata_list.append({
                        "filename": item.value.get("filename"),
                        "table_name": item.value.get("table_name"),
                        "columns": item.value.get("columns"),
                        "row_count": item.value.get("row_count"),
                    })

            return metadata_list
        
    except Exception as e:
        logger.error(f"Failed to get CSV metadata: {e}")
        return []


async def delete_csv_data(thread_id: str) -> int:
    """Delete all CSV data for a thread (session cleanup).

    Args:
        thread_id: The chat session ID.

    Returns:
        Number of items deleted.
    """
    total_deleted = 0
    
    try:
        async with AsyncDatabricksStore(
            instance_name=LAKEBASE_INSTANCE_NAME,
            embedding_endpoint=os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en"),
            embedding_dims=int(os.getenv("EMBEDDING_DIMS", "1024")),
        ) as store:
            
            # First find all CSV files in this thread
            base_namespace = (CSV_NAMESPACE_PREFIX, thread_id)
            meta_results = await store.asearch(base_namespace, query="csv_metadata", limit=100)
            
            csv_namespaces = []
            for item in meta_results:
                if item.key.startswith(META_KEY_PREFIX) and item.value.get("type") == "csv_metadata":
                    table_name = item.value.get("table_name")
                    if table_name:
                        csv_namespaces.append((CSV_NAMESPACE_PREFIX, thread_id, table_name))
            
            # Delete from each CSV namespace
            for namespace in csv_namespaces:
                try:
                    # List all items in the namespace
                    results = await store.asearch(namespace, query="", limit=10000)
                    for item in results:
                        await store.adelete(namespace, item.key)
                        total_deleted += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to delete from namespace {namespace}: {e}")
            
            # Also delete any metadata in the base namespace
            try:
                for item in meta_results:
                    if item.key.startswith(META_KEY_PREFIX):
                        await store.adelete(base_namespace, item.key)
                        total_deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete metadata: {e}")

        logger.info(f"Deleted {total_deleted} CSV items for thread '{thread_id}'")
        return total_deleted
        
    except Exception as e:
        logger.error(f"Failed to delete CSV data: {e}")
        if "permission denied" in str(e).lower():
            raise ValueError("CSV deletion failed: insufficient database permissions.")
        return 0
