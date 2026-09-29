"""
Skill: draft a response to a user/customer question, given retrieved
context. Distinct from the retrieval agent's own generation in that
this is meant to be reusable across agents (e.g. action_agent may also
need to draft a message after taking an action).
"""


def draft_response(question: str, context: str, tone: str = "professional") -> str:
    """
    Wire up the model call here. Consider loading the tone/style
    guidance from prompts/ so it's easy for a client to customize
    brand voice without touching code.
    """
    raise NotImplementedError("Wire up the model call for this skill")
