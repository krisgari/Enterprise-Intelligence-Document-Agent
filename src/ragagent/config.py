"""
Central configuration for RagAgent.
Loads settings from environment variables (see .env.example).
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Absolute path to the project root, so path-based settings below work
# regardless of the current working directory the app is launched from
# (e.g. running `uvicorn` from src/ vs. running scripts from the repo
# root previously pointed at two different "data/" directories).
# RAGAGENT_ROOT is .../RagAgent (three levels up from this file:
# config.py -> ragagent -> src -> RagAgent).
_RAGAGENT_ROOT = Path(__file__).resolve().parent.parent.parent
_TICKETING_SERVER_PATH = str(_RAGAGENT_ROOT / "mcp_servers" / "ticketing_server.py")

# Load .env from the project root regardless of the current working
# directory the app was launched from (fixes ANTHROPIC_API_KEY and other
# settings silently not being picked up when running e.g. `cd src &&
# uvicorn ...` instead of from the repo root).
load_dotenv(_RAGAGENT_ROOT / ".env")


def _abs_path(env_var: str, default_relative: str) -> str:
    """
    Resolve a path setting to an absolute path anchored at the project
    root, regardless of whether it comes from the env var or the built-in
    default, and regardless of what directory the process is launched
    from. A relative value (the common case, e.g. "data/vectorstore") is
    joined onto the project root; an already-absolute value is used as-is
    so users can still point somewhere else entirely if they want to.
    """
    value = os.getenv(env_var) or default_relative
    value_path = Path(value)
    if value_path.is_absolute():
        return str(value_path)
    return str(_RAGAGENT_ROOT / value_path)


@dataclass
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model_name: str = os.getenv("RAGAGENT_MODEL", "claude-sonnet-4-5-20250929")

    # Retrieval settings
    chunk_size: int = int(os.getenv("RAGAGENT_CHUNK_SIZE", "800"))
    chunk_overlap: int = int(os.getenv("RAGAGENT_CHUNK_OVERLAP", "100"))
    top_k: int = int(os.getenv("RAGAGENT_TOP_K", "5"))
    embedding_model: str = os.getenv("RAGAGENT_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # Paths — absolute by default (anchored to the project root), so they
    # work the same whether you launch from the repo root or from src/.
    raw_data_dir: str = field(default_factory=lambda: _abs_path("RAGAGENT_RAW_DIR", "data/raw"))
    processed_data_dir: str = field(default_factory=lambda: _abs_path("RAGAGENT_PROCESSED_DIR", "data/processed"))

    # ChromaDB — either connect to a Chroma server (host/port) for a
    # multi-service/enterprise deployment, or fall back to an embedded
    # local persistent client (persist_directory) for local dev.
    chroma_host: str | None = os.getenv("CHROMA_HOST") or None
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8001"))
    chroma_persist_directory: str = field(
        default_factory=lambda: _abs_path("CHROMA_PERSIST_DIR", "data/vectorstore")
    )
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION", "ragagent_docs")

    # LangSmith / LangChain tracing
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    langsmith_project: str = os.getenv("LANGSMITH_PROJECT", "ragagent")
    langsmith_tracing_enabled: bool = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

    # MCP servers this agent can connect to. Each entry follows the
    # config shape expected by langchain_mcp_adapters.MultiServerMCPClient.
    # "ticketing" points at the bundled sample server (mcp_servers/ticketing_server.py)
    # so action_agent works out of the box — add more servers here as you build them.
    mcp_servers: dict = field(default_factory=lambda: {
        "ticketing": {
            "command": "python",
            "args": [_TICKETING_SERVER_PATH],
            "transport": "stdio",
        },
    })


settings = Settings()
