"""
Validates incoming user input before it reaches any agent.

Two concerns kept separate on purpose:
- PII detection: don't let sensitive data flow into logs/prompts unnecessarily.
- Prompt injection detection: catch attempts (often embedded in retrieved
  documents or user input) to override the system prompt or exfiltrate
  instructions.
"""
import re
from dataclasses import dataclass

from ragagent.guardrails.policies import GuardrailPolicy, default_policy

# Simple illustrative patterns; swap for a real PII-detection library
# (e.g. Microsoft Presidio) for production use.
_PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}


@dataclass
class InputCheckResult:
    allowed: bool
    reason: str | None = None
    detected_pii_types: list[str] | None = None


def check_input(text: str, policy: GuardrailPolicy = default_policy) -> InputCheckResult:
    if policy.block_pii:
        detected = [name for name, pattern in _PII_PATTERNS.items() if pattern.search(text)]
        if detected:
            return InputCheckResult(
                allowed=False,
                reason="Input appears to contain PII",
                detected_pii_types=detected,
            )

    lowered = text.lower()
    for pattern in policy.block_prompt_injection_patterns:
        if pattern in lowered:
            return InputCheckResult(
                allowed=False,
                reason=f"Potential prompt injection detected: '{pattern}'",
            )

    return InputCheckResult(allowed=True)
