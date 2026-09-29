"""
Central place to register tools the agent can call.
Keeping registration separate from tool implementation makes it easy
to see, at a glance, everything an agent is allowed to do.
"""
from typing import Callable, Dict


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    def register(self, name: str, fn: Callable) -> None:
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
        self._tools[name] = fn

    def get(self, name: str) -> Callable:
        if name not in self._tools:
            raise KeyError(f"No tool registered under '{name}'")
        return self._tools[name]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())


# Example usage (uncomment once you have real tools):
# from ragagent.tools.search_tool import web_search
# registry = ToolRegistry()
# registry.register("web_search", web_search)
registry = ToolRegistry()
