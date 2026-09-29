"""
Request/response models for the API. Keeping these separate from
route handlers makes it easy to reuse/version schemas.
"""
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None


class QueryResponse(BaseModel):
    allowed: bool
    result: str | dict | None = None
    reason: str | None = None
    trace_id: str
    intent: str | None = None


class IngestRequest(BaseModel):
    directory: str | None = None  # defaults to settings.raw_data_dir


class IngestResponse(BaseModel):
    documents_loaded: int
    chunks_created: int


class FeedbackRequest(BaseModel):
    trace_id: str
    rating: int  # e.g. 1-5, or thumbs up/down as 1/0
    comment: str | None = None


class TraceResponse(BaseModel):
    trace_id: str
    duration_ms: float | None
    spans: list[dict]
