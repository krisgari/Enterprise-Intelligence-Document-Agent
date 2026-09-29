"""
MCP client wrapper using the official langchain-mcp-adapters library,
which converts MCP tools into LangChain-compatible tools your LangGraph
agents can call directly (via bind_tools / create_react_agent).

This is genuinely the standard way to bridge MCP <-> LangChain/LangGraph
as of late 2025/2026, rather than a hand-rolled protocol implementation.
"""
from langchain_mcp_adapters.client import MultiServerMCPClient

from ragagent.config import settings
from ragagent.observability.retry import mcp_retry

_client: MultiServerMCPClient | None = None


def get_mcp_client() -> MultiServerMCPClient:
    """
    Returns a singleton MultiServerMCPClient configured from
    settings.mcp_servers (see config.py and .env for how to add servers).
    """
    global _client
    if _client is None:
        _client = MultiServerMCPClient(settings.mcp_servers)
    return _client


@mcp_retry
async def get_mcp_tools():
    """
    Loads and returns LangChain-compatible tools from all configured MCP
    servers. Call this once at startup (or lazily on first use) and pass
    the result into create_react_agent() or bind_tools().

    Retried on transient connection failures (e.g. the ticketing server's
    subprocess hasn't finished starting yet) — safe to retry because
    listing available tools has no side effects, unlike actually calling
    one of them.
    """
    client = get_mcp_client()
    return await client.get_tools()
