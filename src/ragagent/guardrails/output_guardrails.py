"""
Validates agent output before it's returned to the user.

Checks:
- confidence thresholding: low-confidence answers get flagged for
  human review instead of auto-returned.
- citation requirement: answers should reference their source when
  the policy requires it (helps prevent unattributed hallucination).
- blocked topics: refuse to answer on topics outside the agent's scope.
"""
from dataclasses import dataclass

from ragagent.guardrails.policies import GuardrailPolicy, default_policy


@dataclass
class OutputCheckResult:
    allowed: bool
    needs_human_review: bool = False
    reason: str | None = None


def check_output(
    answer: str,
    confidence: float,
    has_citation: bool,
    topic: str | None = None,
    policy: GuardrailPolicy = default_policy,
) -> OutputCheckResult:
    if topic and topic in policy.blocked_topics:
        return OutputCheckResult(
            allowed=False,
            reason=f"Topic '{topic}' is out of scope for this agent",
        )

    if confidence < policy.min_confidence_to_auto_answer:
        return OutputCheckResult(
            allowed=True,
            needs_human_review=True,
            reason=f"Confidence {confidence:.2f} below threshold "
            f"{policy.min_confidence_to_auto_answer}",
        )

    if policy.require_citation and not has_citation:
        return OutputCheckResult(
            allowed=True,
            needs_human_review=True,
            reason="Answer is missing a citation",
        )

    return OutputCheckResult(allowed=True)
