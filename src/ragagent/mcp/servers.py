"""
Example MCP server configuration, in the shape expected by
langchain_mcp_adapters.MultiServerMCPClient (see mcp/client.py).

This is duplicated from config.py's default for documentation purposes —
config.py's `settings.mcp_servers` is the actual source of truth used at
runtime. Copy entries from here into your .env-driven config or directly
into config.py once you have real MCP servers to connect to.

Example entries:

MCP_SERVERS_EXAMPLE = {
    "ticketing": {
        "command": "python",
        "args": ["/path/to/ticketing_mcp_server.py"],
        "transport": "stdio",
    },
    "calendar": {
        "url": "http://localhost:8101/mcp",
        "transport": "streamable_http",
    },
}
"""
from ragagent.config import settings

MCP_SERVERS = settings.mcp_servers

