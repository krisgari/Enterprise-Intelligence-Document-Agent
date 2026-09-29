"""
POST /ingest — triggers loading, chunking, and adding documents from a
given directory into the Chroma vector store.
"""
from fastapi import APIRouter

from ragagent.api.schemas import IngestRequest, IngestResponse
from ragagent.config import settings
from ragagent.retrieval.loader import load_documents
from ragagent.retrieval.chunker import chunk_text
from ragagent.retrieval.vectorstore import get_vectorstore

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    directory = request.directory or settings.raw_data_dir
    tenant_id = request.tenant_id or settings.default_tenant_id
    docs = load_documents(directory)

    all_chunks = []
    for doc in docs:
        chunks = chunk_text(
            doc["text"],
            source=doc["source"],
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        all_chunks.extend(chunks)

    if all_chunks:
        store = get_vectorstore()
        texts = [c.text for c in all_chunks]
        metadatas = [
            {"source": c.source, "chunk_id": c.chunk_id, "tenant_id": tenant_id}
            for c in all_chunks
        ]
        store.add_texts(texts=texts, metadatas=metadatas)

    return IngestResponse(documents_loaded=len(docs), chunks_created=len(all_chunks))
