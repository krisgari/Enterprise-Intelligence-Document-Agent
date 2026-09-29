"""
Skill: escalate a request to a human, with full context attached.
This is the "safety valve" skill other agents/guardrails call into
when confidence is low, compliance fails, or the request is out of scope.
"""
from dataclasses import dataclass


@dataclass
class EscalationRecord:
    reason: str
    original_input: str
    agent_output: str | None
    trace_id: str | None = None


def escalate(reason: str, original_input: str, agent_output: str | None = None,
             trace_id: str | None = None) -> EscalationRecord:
    """
    Record an escalation. Wire this up to write into whatever your
    client's human-review queue is (a DB table, a ticketing system via
    MCP, a Slack webhook, etc.).
    """
    record = EscalationRecord(
        reason=reason,
        original_input=original_input,
        agent_output=agent_output,
        trace_id=trace_id,
    )
    # TODO: persist / notify (e.g. write to DB, call MCP ticketing tool)
    return record
