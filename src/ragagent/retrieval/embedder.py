"""
Embeddings, via LangChain's HuggingFaceEmbeddings wrapper around a local
sentence-transformers model. Implements the langchain_core.embeddings.Embeddings
interface, so it plugs directly into Chroma (or any other LangChain
vector store) with no glue code.

No external embedding API key required — the model runs locally.
Swap `embedding_model` in .env for a different sentence-transformers
model, or replace this file with e.g. VoyageAIEmbeddings /
OpenAIEmbeddings for a hosted alternative.
"""
from langchain_huggingface import HuggingFaceEmbeddings

from ragagent.config import settings


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Returns a LangChain Embeddings instance, ready to pass to a
    vector store (Chroma.from_texts(..., embedding=get_embeddings())
    or Chroma(..., embedding_function=get_embeddings())).
    """
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)
