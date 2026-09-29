"""
Agent that takes real actions via MCP tools (e.g. create a ticket,
update a record), built on LangGraph's prebuilt ReAct agent so tool
selection/looping is handled by a battle-tested implementation rather
than hand-rolled intent parsing.
"""
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from ragagent.agents.base_agent import BaseAgent
from ragagent.mcp.client import get_mcp_tools
from ragagent.config import settings


class ActionAgent(BaseAgent):
    name = "action_agent"

    def __init__(self, llm: ChatAnthropic | None = None):
        self.llm = llm or ChatAnthropic(
            model=settings.model_name,
            anthropic_api_key=settings.anthropic_api_key,
            max_tokens=1000,
        )
        self._agent = None  # built lazily since tool loading is async

    async def _ensure_agent(self):
        if self._agent is None:
            tools = await get_mcp_tools()
            if not tools:
                raise RuntimeError(
                    "No MCP tools configured. Add servers to settings.mcp_servers "
                    "(see config.py / mcp/servers.py) before using ActionAgent."
                )
            self._agent = create_react_agent(self.llm, tools)
        return self._agent

    async def arun(self, user_input: str, **kwargs) -> dict:
        agent = await self._ensure_agent()
        result = await agent.ainvoke({"messages": [{"role": "user", "content": user_input}]})
        final_message = result["messages"][-1]
        return {"answer": final_message.content}

    def run(self, user_input: str, **kwargs) -> dict:
        """
        Sync wrapper for callers that aren't already in an event loop
        (e.g. a plain script). If you're calling this from inside FastAPI
        or another async context, use arun() directly instead.
        """
        import asyncio
        return asyncio.run(self.arun(user_input, **kwargs))
