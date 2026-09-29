"""
Example tool: query the vector store directly as a callable tool
(useful if you expose it to the model as a function/tool call,
separate from the internal Retriever used by RetrievalAgent).
"""
from ragagent.retrieval.retriever import Retriever

_retriever = Retriever()


def query_vectorstore(query: str, top_k: int = 5) -> list[str]:
    """Return the top_k most relevant chunks of text for a query."""
    chunks = _retriever.retrieve(query, top_k=top_k)
    return [c.text for c in chunks]
