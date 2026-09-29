"""
FastAPI app entry point.
Run with: uvicorn ragagent.api.app:app --reload
"""
from fastapi import Depends, FastAPI

from ragagent.observability.langsmith_setup import configure_langsmith
from ragagent.api.auth import require_api_key
from ragagent.api.routes import query, ingest, feedback, traces

configure_langsmith()

app = FastAPI(
    title="RagAgent API",
    description="Document intelligence agent: LangGraph orchestration + Chroma RAG + MCP actions",
    version="0.2.0",
)

# Every route except /health requires a valid X-API-Key (see api/auth.py).
# /health stays open so uptime checks / load balancers don't need a key.
_auth = [Depends(require_api_key)]

app.include_router(query.router, tags=["query"], dependencies=_auth)
app.include_router(ingest.router, tags=["ingest"], dependencies=_auth)
app.include_router(feedback.router, tags=["feedback"], dependencies=_auth)
app.include_router(traces.router, tags=["traces"], dependencies=_auth)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
