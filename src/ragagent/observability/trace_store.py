"""
Exposes trace data for the /traces/{id} endpoint.
Currently backed by the in-memory Tracer; swap for a persistent
store (SQLite/Postgres) if you need traces to survive restarts.
"""
from ragagent.observability.tracer import tracer


def get_trace_dict(trace_id: str) -> dict | None:
    trace = tracer.get_trace(trace_id)
    if trace is None:
        return None
    return trace.to_dict()
