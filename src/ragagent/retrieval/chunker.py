"""
Splits documents into overlapping chunks suitable for embedding.
"""
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    source: str
    chunk_id: int


def chunk_text(text: str, source: str, chunk_size: int = 800, overlap: int = 100) -> list[Chunk]:
    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = start + chunk_size
        chunk_text_ = text[start:end]
        chunks.append(Chunk(text=chunk_text_, source=source, chunk_id=idx))
        start += chunk_size - overlap
        idx += 1
    return chunks
