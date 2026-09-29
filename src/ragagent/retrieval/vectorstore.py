"""
Vector store backed by ChromaDB via the official langchain_chroma
integration.

Two deployment modes, controlled by config/.env:
- CHROMA_HOST set: connects to a standalone Chroma server (docker-compose
  runs one) — the right mode for a real multi-service deployment where
  the vector store needs to survive independently of the API process
  and potentially be shared across multiple API replicas.
- CHROMA_HOST unset: uses an embedded local persistent client, writing
  to CHROMA_PERSIST_DIR — simplest for local development.
"""
from langchain_chroma import Chroma

from ragagent.config import settings
from ragagent.retrieval.embedder import get_embeddings

_vectorstore: Chroma | None = None


def get_vectorstore() -> Chroma:
    """
    Returns a singleton Chroma vectorstore instance, connected either to
    a remote Chroma server or an embedded local persistent store,
    depending on config.
    """
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    embeddings = get_embeddings()

    if settings.chroma_host:
        _vectorstore = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=embeddings,
            host=settings.chroma_host,
            port=settings.chroma_port,
        )
    else:
        _vectorstore = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=embeddings,
            persist_directory=settings.chroma_persist_directory,
        )

    return _vectorstore


def reset_vectorstore_singleton() -> None:
    """Useful in tests to force re-reading config on the next get_vectorstore() call."""
    global _vectorstore
    _vectorstore = None
