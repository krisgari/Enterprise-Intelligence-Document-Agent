"""
Configurable rules used by input/output guardrails.
Keeping these as data (not hardcoded logic) makes it easy for a client
to tune thresholds without touching guardrail code.
"""
from dataclasses import dataclass, field


@dataclass
class GuardrailPolicy:
    # Input guardrails
    block_pii: bool = True
    block_prompt_injection_patterns: list[str] = field(
        default_factory=lambda: [
            "ignore previous instructions",
            "disregard all prior",
            "you are now",
            "system prompt:",
        ]
    )

    # Output guardrails
    min_confidence_to_auto_answer: float = 0.6
    require_citation: bool = True
    blocked_topics: list[str] = field(default_factory=list)


default_policy = GuardrailPolicy()
