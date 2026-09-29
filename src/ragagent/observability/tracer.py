"""
Lightweight tracing: creates a trace per request, with spans for each
significant step (retrieval, tool call, generation, guardrail check).

Not a replacement for OpenTelemetry in a real production system, but
gives you the same mental model (trace -> spans -> attributes) so you
can swap in OTel later without changing how the rest of the code calls it.
"""
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    name: str
    start_time: float
    end_time: float | None = None
    attributes: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float | None:
        if self.end_time is None:
            return None
        return round((self.end_time - self.start_time) * 1000, 2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
        }


@dataclass
class Trace:
    trace_id: str
    spans: list[Span] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "duration_ms": round((self.end_time - self.start_time) * 1000, 2)
            if self.end_time
            else None,
            "spans": [s.to_dict() for s in self.spans],
        }


class Tracer:
    def __init__(self):
        self._traces: dict[str, Trace] = {}

    def start_trace(self, trace_id: str | None = None) -> Trace:
        trace_id = trace_id or str(uuid.uuid4())
        trace = Trace(trace_id=trace_id)
        self._traces[trace_id] = trace
        return trace

    def end_trace(self, trace_id: str) -> None:
        trace = self._traces.get(trace_id)
        if trace:
            trace.end_time = time.time()

    def get_trace(self, trace_id: str) -> Trace | None:
        return self._traces.get(trace_id)

    @contextmanager
    def span(self, trace_id: str, name: str, **attributes: Any):
        """
        Usage:
            with tracer.span(trace_id, "retrieval", query=query, top_k=5):
                chunks = retriever.retrieve(query)
        """
        span = Span(name=name, start_time=time.time(), attributes=dict(attributes))
        try:
            yield span
        finally:
            span.end_time = time.time()
            trace = self._traces.get(trace_id)
            if trace:
                trace.spans.append(span)


# Module-level singleton, simplest option for a single-process app.
# Swap for a shared store (Redis, DB) if you scale to multiple workers.
tracer = Tracer()
