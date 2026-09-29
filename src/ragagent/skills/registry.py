"""
Skills are composed capabilities: they combine a prompt template,
optionally one or more tools, and produce a specific kind of output
(e.g. "summarize a policy document", "draft a customer response").

This is deliberately kept separate from tools/registry.py:
- a "tool" is a single callable capability (search, query vector store)
- a "skill" is a higher-level behavior an agent invokes, which may
  internally use one or more tools plus a specific prompt
"""
from typing import Callable, Dict


class SkillRegistry:
    def __init__(self):
        self._skills: Dict[str, Callable] = {}

    def register(self, name: str, fn: Callable) -> None:
        if name in self._skills:
            raise ValueError(f"Skill '{name}' is already registered")
        self._skills[name] = fn

    def get(self, name: str) -> Callable:
        if name not in self._skills:
            raise KeyError(f"No skill registered under '{name}'")
        return self._skills[name]

    def list_skills(self) -> list[str]:
        return list(self._skills.keys())


registry = SkillRegistry()

# Register built-in skills (uncomment as you implement each one):
# from ragagent.skills.summarize_policy import summarize_policy
# from ragagent.skills.check_compliance import check_compliance
# from ragagent.skills.draft_response import draft_response
# from ragagent.skills.escalate import escalate
#
# registry.register("summarize_policy", summarize_policy)
# registry.register("check_compliance", check_compliance)
# registry.register("draft_response", draft_response)
# registry.register("escalate", escalate)
