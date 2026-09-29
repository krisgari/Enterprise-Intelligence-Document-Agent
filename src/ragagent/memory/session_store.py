"""
Simple in-memory conversation store, keyed by session id.
Swap for Redis/DB-backed storage for production/multi-user use.
"""
from dataclasses import dataclass, field


@dataclass
class SessionStore:
    _sessions: dict = field(default_factory=dict)

    def get_history(self, session_id: str) -> list[dict]:
        return self._sessions.get(session_id, [])

    def append(self, session_id: str, role: str, content: str) -> None:
        self._sessions.setdefault(session_id, []).append(
            {"role": role, "content": content}
        )

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
