"""
GET /traces/{trace_id} — returns the full span breakdown for a given
request, for debugging and the dashboard UI.
"""
from fastapi import APIRouter, HTTPException

from ragagent.api.schemas import TraceResponse
from ragagent.observability.trace_store import get_trace_dict

router = APIRouter()


@router.get("/traces/{trace_id}", response_model=TraceResponse)
def get_trace(trace_id: str) -> TraceResponse:
    trace = get_trace_dict(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return TraceResponse(**trace)
