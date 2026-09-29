import pytest
from ragagent.tools.registry import ToolRegistry


def test_registry_register_and_get():
    registry = ToolRegistry()
    registry.register("noop", lambda: "ok")
    assert registry.get("noop")() == "ok"


def test_registry_duplicate_raises():
    registry = ToolRegistry()
    registry.register("noop", lambda: "ok")
    with pytest.raises(ValueError):
        registry.register("noop", lambda: "again")


def test_registry_missing_raises():
    registry = ToolRegistry()
    with pytest.raises(KeyError):
        registry.get("missing")
