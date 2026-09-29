"""
Loads raw documents (pdf, txt, md, docx, etc.) from data/raw
into plain text ready for chunking.
"""
from pathlib import Path


def load_documents(raw_dir: str) -> list[dict]:
    """
    Returns a list of {"source": filename, "text": content} dicts.
    Extend this to handle PDFs, docx, html, etc. as needed
    (e.g. using pypdf, python-docx, BeautifulSoup).
    """
    docs = []
    for path in Path(raw_dir).glob("**/*"):
        if path.is_file() and path.suffix in {".txt", ".md"}:
            docs.append({"source": str(path), "text": path.read_text(encoding="utf-8")})
    return docs
