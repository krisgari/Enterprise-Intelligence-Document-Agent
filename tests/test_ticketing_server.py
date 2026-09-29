"""
Tests the ticketing server's tool functions directly (as plain Python
functions), without going through the MCP protocol/transport — the
@mcp.tool() decorator registers the function but still returns it
callable, so this is a fast, realistic unit test of the actual logic
the MCP server exposes.

Requires the `mcp` package (skips cleanly if not installed).
"""
import sys
import tempfile
from pathlib import Path

import pytest

pytest.importorskip("mcp")

sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_servers"))


@pytest.fixture
def ticketing_module(monkeypatch, tmp_path):
    """Import the server module fresh, pointed at a temp data file, per test."""
    import importlib
    import ticketing_server

    importlib.reload(ticketing_server)
    monkeypatch.setattr(ticketing_server, "_DATA_FILE", tmp_path / "tickets_data.json")
    return ticketing_server


def test_create_ticket_returns_generated_id(ticketing_module):
    ticket = ticketing_module.create_ticket(title="Broken login", description="Details here")
    assert ticket["id"] == "TICKET-1000"
    assert ticket["status"] == "open"
    assert ticket["priority"] == "normal"


def test_create_ticket_rejects_invalid_priority(ticketing_module):
    result = ticketing_module.create_ticket(title="X", description="Y", priority="critical")
    assert "error" in result


def test_get_ticket_roundtrip(ticketing_module):
    created = ticketing_module.create_ticket(title="X", description="Y")
    fetched = ticketing_module.get_ticket(created["id"])
    assert fetched == created


def test_get_ticket_missing_returns_error(ticketing_module):
    result = ticketing_module.get_ticket("TICKET-9999")
    assert "error" in result


def test_list_tickets_filters_by_status(ticketing_module):
    t1 = ticketing_module.create_ticket(title="A", description="a")
    t2 = ticketing_module.create_ticket(title="B", description="b")
    ticketing_module.update_ticket_status(t2["id"], "closed")

    open_tickets = ticketing_module.list_tickets(status="open")
    closed_tickets = ticketing_module.list_tickets(status="closed")

    assert len(open_tickets) == 1
    assert open_tickets[0]["id"] == t1["id"]
    assert len(closed_tickets) == 1
    assert closed_tickets[0]["id"] == t2["id"]


def test_update_ticket_status_persists(ticketing_module):
    t = ticketing_module.create_ticket(title="A", description="a")
    ticketing_module.update_ticket_status(t["id"], "in_progress")
    fetched = ticketing_module.get_ticket(t["id"])
    assert fetched["status"] == "in_progress"


def test_update_ticket_status_rejects_invalid_status(ticketing_module):
    t = ticketing_module.create_ticket(title="A", description="a")
    result = ticketing_module.update_ticket_status(t["id"], "archived")
    assert "error" in result


def test_state_persists_across_module_reloads(ticketing_module, tmp_path):
    """Confirms tickets survive a fresh 'process' (module reload) reading the same file."""
    import importlib
    import ticketing_server

    t = ticketing_module.create_ticket(title="Persisted", description="d")

    importlib.reload(ticketing_server)
    ticketing_server._DATA_FILE = tmp_path / "tickets_data.json"

    fetched = ticketing_server.get_ticket(t["id"])
    assert fetched["title"] == "Persisted"
