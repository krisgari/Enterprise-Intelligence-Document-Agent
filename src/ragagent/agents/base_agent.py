"""
Shared interface that all agents implement.
Keeping this abstract lets you swap agent implementations without
touching orchestration or tool code.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Common contract for all agents in this project."""

    name: str = "base_agent"

    @abstractmethod
    def run(self, user_input: str, **kwargs) -> Any:
        """
        Execute the agent on a single user input.
        Return whatever the caller expects (str, dict, etc.).
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
