"""
Skill: summarize a policy document (or retrieved chunks about a policy)
into a short, plain-language summary.
"""


def summarize_policy(context: str) -> str:
    """
    Given retrieved policy text, produce a plain-language summary.
    Wire up the actual model call here (via your Anthropic client),
    using a dedicated prompt template if you want one separate from
    the general retrieval prompt.
    """
    raise NotImplementedError("Wire up the model call for this skill")
