"""RAG stubs: chunking, embeddings, vector search.

Plug in Chroma, pgvector, or another store here. Vector DB is out of
scope for Week 1 SQLite; keep embeddings out of the SQL models.
"""

from typing import Any


def chunk_text(text: str) -> list[str]:
    raise NotImplementedError("Implement document chunking")


def embed(texts: list[str]) -> list[list[float]]:
    raise NotImplementedError("Implement embedding calls")


def search(query: str, k: int = 8) -> list[dict[str, Any]]:
    """Return retrieved chunks: id, text, score. Not implemented."""
    raise NotImplementedError("Implement vector search / retrieval")
