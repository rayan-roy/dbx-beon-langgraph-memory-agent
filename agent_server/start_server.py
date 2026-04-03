from dotenv import load_dotenv
from fastapi import Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from mlflow.genai.agent_server import AgentServer, setup_mlflow_git_based_version_tracking

# Load env vars from .env before importing the agent for proper auth
load_dotenv(dotenv_path=".env", override=True)

# Need to import the agent to register the functions with the server
import agent_server.agent  # noqa: E402

from agent_server.csv_store import delete_csv_data, get_csv_metadata, ingest_csv  # noqa: E402


class PlotRequest(BaseModel):
    content: str
    history: Optional[List[Dict]] = []
    thread_id: Optional[str] = None

agent_server = AgentServer("ResponsesAgent", enable_chat_proxy=True)

# Define the app as a module level variable to enable multiple workers
app = agent_server.app  # noqa: F841
try:
    setup_mlflow_git_based_version_tracking()
except Exception:
    pass  # Non-critical; may fail on some MLflow versions


@app.post("/upload-csv")
async def upload_csv(file: UploadFile, thread_id: str = Form(...)):
    """Upload a CSV file and store its rows as embeddings scoped to the thread."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    try:
        csv_content = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded CSV.")

    try:
        result = await ingest_csv(thread_id, csv_content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@app.delete("/cleanup-csv/{thread_id}")
async def cleanup_csv(thread_id: str):
    """Delete all CSV data for a thread (session cleanup)."""
    count = await delete_csv_data(thread_id)
    return {"thread_id": thread_id, "deleted_count": count}


@app.get("/csv-metadata/{thread_id}")
async def csv_metadata(thread_id: str):
    """Return metadata about uploaded CSVs in a thread."""
    metadata = await get_csv_metadata(thread_id)
    return {"thread_id": thread_id, "files": metadata}


@app.post("/api/agent/plot")
async def generate_plot(request: PlotRequest):
    """Generate a chart specification from agent response content."""
    try:
        from agent_server.plot_agent import create_plot_spec
        
        spec = await create_plot_spec(
            content=request.content, 
            history=request.history, 
            thread_id=request.thread_id
        )
        return JSONResponse(content=spec)
    except Exception as e:
        import logging
        logging.error(f"Plot generation error: {e}", exc_info=True)
        return JSONResponse(
            content={"no_data": True, "reason": f"Error generating chart: {str(e)}"}, 
            status_code=500
        )


def main():
    agent_server.run(app_import_string="agent_server.start_server:app")
