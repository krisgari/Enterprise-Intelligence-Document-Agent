import pytest
from ragagent.skills.registry import SkillRegistry
from ragagent.skills.escalate import escalate


def test_skill_registry_register_and_get():
    registry = SkillRegistry()
    registry.register("noop", lambda: "ok")
    assert registry.get("noop")() == "ok"


def test_skill_registry_duplicate_raises():
    registry = SkillRegistry()
    registry.register("noop", lambda: "ok")
    with pytest.raises(ValueError):
        registry.register("noop", lambda: "again")


def test_escalate_returns_record():
    record = escalate(reason="low confidence", original_input="what is X?",
                       agent_output="maybe X is...", trace_id="abc123")
    assert record.reason == "low confidence"
    assert record.trace_id == "abc123"
