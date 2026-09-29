"""
Queries the Chroma vector store for the most relevant chunks given a question.
"""
from dataclasses import dataclass

from ragagent.config import settings
from ragagent.retrieval.vectorstore import get_vectorstore


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


class Retriever:
    def __init__(self):
        self.vectorstore = get_vectorstore()

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        tenant_id: str | None = None,
    ) -> list[RetrievedChunk]:
        """
        Embed the query (handled internally by Chroma's embedding_function)
        and return the top_k most relevant chunks with similarity scores.

        tenant_id scopes the search to chunks ingested under that tenant
        (via a Chroma metadata filter), so multiple tenants can share one
        collection without seeing each other's data. Defaults to
        settings.default_tenant_id, so single-tenant use is unaffected.
        Chunks ingested before multi-tenancy was added (with no tenant_id
        metadata) won't match a tenant-scoped filter — re-ingest them to
        pick up a tenant_id.
        """
        top_k = top_k or settings.top_k
        tenant_id = tenant_id or settings.default_tenant_id
        results = self.vectorstore.similarity_search_with_score(
            query, k=top_k, filter={"tenant_id": tenant_id},
        )
        return [
            RetrievedChunk(
                text=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                # Chroma returns a distance (lower = more similar) by default;
                # convert to a 0-1 "similarity-ish" score for readability.
                score=1.0 / (1.0 + distance),
            )
            for doc, distance in results
        ]

    def as_langchain_retriever(self, top_k: int | None = None, tenant_id: str | None = None):
        """Expose a native LangChain retriever, useful for LCEL chains or LangGraph nodes."""
        tenant_id = tenant_id or settings.default_tenant_id
        return self.vectorstore.as_retriever(
            search_kwargs={"k": top_k or settings.top_k, "filter": {"tenant_id": tenant_id}},
        )
