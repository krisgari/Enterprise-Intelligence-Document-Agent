"""
FastAPI app entry point.
Run with: uvicorn ragagent.api.app:app --reload
"""
from fastapi import FastAPI

from ragagent.observability.langsmith_setup import configure_langsmith
from ragagent.api.routes import query, ingest, feedback, traces

configure_langsmith()

app = FastAPI(
    title="RagAgent API",
    description="Document intelligence agent: LangGraph orchestration + Chroma RAG + MCP actions",
    version="0.2.0",
)

app.include_router(query.router, tags=["query"])
app.include_router(ingest.router, tags=["ingest"])
app.include_router(feedback.router, tags=["feedback"])
app.include_router(traces.router, tags=["traces"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
