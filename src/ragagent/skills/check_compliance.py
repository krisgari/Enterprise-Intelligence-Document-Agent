"""
Skill: check whether a proposed action or statement complies with
retrieved policy context. Returns a structured verdict rather than
free text, so calling code (e.g. guardrails) can act on it directly.
"""
from dataclasses import dataclass


@dataclass
class ComplianceResult:
    compliant: bool
    reasoning: str
    cited_sources: list[str]


def check_compliance(statement: str, policy_context: str) -> ComplianceResult:
    """
    Wire up a model call that returns a structured judgment.
    Consider using the Anthropic SDK's structured output / tool-use
    pattern here so the result reliably parses into ComplianceResult.
    """
    raise NotImplementedError("Wire up the model call for this skill")
