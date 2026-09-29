"""
A real, standalone MCP server exposing a small ticketing system as tools.

Run directly for a quick manual check:
    python mcp_servers/ticketing_server.py
(it will sit waiting for a stdio client — Ctrl+C to exit)

In practice this is launched automatically by langchain_mcp_adapters'
MultiServerMCPClient (see config.py's `mcp_servers` and
src/ragagent/mcp/client.py) — you don't run it by hand in normal use.

Storage is persisted to a JSON file next to this script (tickets_data.json),
not just kept in memory. This matters because MCP stdio transport can
spawn a fresh server subprocess per tool call depending on the client
implementation — an in-memory dict would silently lose state between
calls in that case. Swap this for a real database for production use.
"""
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Ticketing")

_DATA_FILE = Path(__file__).parent / "tickets_data.json"

VALID_STATUSES = {"open", "in_progress", "closed"}
VALID_PRIORITIES = {"low", "normal", "high", "urgent"}


def _load() -> dict:
    if not _DATA_FILE.exists():
        return {"tickets": {}, "next_id": 1000}
    with open(_DATA_FILE, "r") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


@mcp.tool()
def create_ticket(title: str, description: str, priority: str = "normal") -> dict:
    """
    Create a new support ticket.

    Args:
        title: Short summary of the issue.
        description: Full details of the issue.
        priority: One of "low", "normal", "high", "urgent". Defaults to "normal".

    Returns:
        The created ticket, including its generated id.
    """
    if priority not in VALID_PRIORITIES:
        return {"error": f"Invalid priority '{priority}'. Must be one of {sorted(VALID_PRIORITIES)}."}

    data = _load()
    ticket_id = f"TICKET-{data['next_id']}"
    data["next_id"] += 1

    ticket = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "open",
    }
    data["tickets"][ticket_id] = ticket
    _save(data)
    return ticket


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """
    Look up a single ticket by its ID.

    Args:
        ticket_id: The ticket ID, e.g. "TICKET-1000".

    Returns:
        The ticket if found, or an error message if not.
    """
    data = _load()
    if ticket_id not in data["tickets"]:
        return {"error": f"No ticket found with id '{ticket_id}'."}
    return data["tickets"][ticket_id]


@mcp.tool()
def list_tickets(status: str = "") -> list[dict]:
    """
    List all tickets, optionally filtered by status.

    Args:
        status: Optional filter — one of "open", "in_progress", "closed".
                Leave empty to list all tickets regardless of status.

    Returns:
        A list of matching tickets.
    """
    data = _load()
    tickets = list(data["tickets"].values())
    if status:
        if status not in VALID_STATUSES:
            return [{"error": f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}."}]
        tickets = [t for t in tickets if t["status"] == status]
    return tickets


@mcp.tool()
def update_ticket_status(ticket_id: str, status: str) -> dict:
    """
    Update a ticket's status.

    Args:
        ticket_id: The ticket ID to update.
        status: New status — one of "open", "in_progress", "closed".

    Returns:
        The updated ticket, or an error message if the ticket or status is invalid.
    """
    data = _load()
    if ticket_id not in data["tickets"]:
        return {"error": f"No ticket found with id '{ticket_id}'."}
    if status not in VALID_STATUSES:
        return {"error": f"Invalid status '{status}'. Must be one of {sorted(VALID_STATUSES)}."}

    data["tickets"][ticket_id]["status"] = status
    _save(data)
    return data["tickets"][ticket_id]


if __name__ == "__main__":
    mcp.run(transport="stdio")
