"""
Demo: exercises ActionAgent against the bundled sample ticketing MCP
server end to end — creates a ticket, lists tickets, and updates status,
all driven by natural-language requests through the ReAct agent loop.

Run with: python scripts/demo_action_agent.py

Requires ANTHROPIC_API_KEY set (the agent uses ChatAnthropic to decide
which MCP tool to call), and the `mcp`, `langchain-mcp-adapters`, and
`langgraph` packages installed.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ragagent.agents.action_agent import ActionAgent

# Reset ticket state so this demo produces the same TICKET-1000 id
# every time it's run, regardless of prior runs.
_TICKETS_DATA_FILE = Path(__file__).parent.parent / "mcp_servers" / "tickets_data.json"
_TICKETS_DATA_FILE.unlink(missing_ok=True)


async def main():
    agent = ActionAgent()

    print("=== 1. Create a ticket ===")
    result = await agent.arun(
        "Create a high priority ticket titled 'Login button broken' "
        "with description 'Users report the login button is unresponsive on mobile Safari'."
    )
    print(result["answer"])

    print("\n=== 2. List open tickets ===")
    result = await agent.arun("List all open tickets.")
    print(result["answer"])

    print("\n=== 3. Update a ticket's status ===")
    result = await agent.arun(
        "Update TICKET-1000 to in_progress status, since someone just started working on it."
    )
    print(result["answer"])

    print("\n=== 4. Confirm the update ===")
    result = await agent.arun("What's the current status of TICKET-1000?")
    print(result["answer"])


if __name__ == "__main__":
    asyncio.run(main())
