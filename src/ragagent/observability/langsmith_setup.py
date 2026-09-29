"""
Configures LangSmith tracing via environment variables, based on our
own Settings object, so tracing can be toggled via .env rather than
scattered os.environ calls.

Once LANGSMITH_TRACING=true and a valid LANGSMITH_API_KEY are set,
every ChatAnthropic call made through LangChain/LangGraph (retrieval_agent,
summarize_agent, action_agent, the router graph) is automatically traced
to your LangSmith project — no per-call instrumentation needed.
"""
import os

from ragagent.config import settings


def configure_langsmith() -> None:
    if not settings.langsmith_tracing_enabled:
        return

    if not settings.langsmith_api_key:
        raise RuntimeError(
            "LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is not set. "
            "Get a key at https://smith.langchain.com and add it to .env."
        )

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
