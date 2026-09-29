"""
One-off script: loads raw documents, chunks them, and adds them to the
Chroma vector store (embedding happens automatically via the store's
configured embedding_function).

Run with: python scripts/ingest.py
Or for a specific tenant: python scripts/ingest.py --tenant-id acme-corp
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ragagent.config import settings
from ragagent.retrieval.loader import load_documents
from ragagent.retrieval.chunker import chunk_text
from ragagent.retrieval.vectorstore import get_vectorstore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tenant-id",
        default=settings.default_tenant_id,
        help=f"Tag ingested chunks with this tenant (default: {settings.default_tenant_id!r}). "
             "Only queries scoped to the same tenant_id will retrieve this data.",
    )
    args = parser.parse_args()

    docs = load_documents(settings.raw_data_dir)
    print(f"Loaded {len(docs)} documents from {settings.raw_data_dir}")

    if not docs:
        print(f"No documents found. Add .txt or .md files to {settings.raw_data_dir}/ and re-run.")
        return

    all_chunks = []
    for doc in docs:
        chunks = chunk_text(
            doc["text"],
            source=doc["source"],
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        all_chunks.extend(chunks)
    print(f"Created {len(all_chunks)} chunks")

    print(f"Embedding + adding to Chroma as tenant '{args.tenant_id}' "
          f"(downloads a small model on first run)...")
    store = get_vectorstore()
    texts = [c.text for c in all_chunks]
    metadatas = [
        {"source": c.source, "chunk_id": c.chunk_id, "tenant_id": args.tenant_id}
        for c in all_chunks
    ]
    store.add_texts(texts=texts, metadatas=metadatas)

    print(f"Ingest complete. {len(all_chunks)} chunks added to collection "
          f"'{settings.chroma_collection_name}' under tenant '{args.tenant_id}'.")


if __name__ == "__main__":
    main()
