"""Build the local FAISS store from agricultural PDFs."""

from .chunker import chunk_pages
from .config import (
    CHUNK_OVERLAP_WORDS,
    CHUNK_SIZE_WORDS,
    DOCUMENTS_DIR,
    EMBEDDING_MODEL_NAME,
    VECTOR_STORE_DIR,
)
from .document_loader import load_pdf_pages
from .embeddings import EmbeddingModel
from .vector_store import VectorStore


def ingest() -> int:
    pages = load_pdf_pages(DOCUMENTS_DIR)
    chunks = chunk_pages(pages, CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS)
    if not chunks:
        raise RuntimeError("No non-empty PDF pages found in the crop document folders")
    vectors = EmbeddingModel(EMBEDDING_MODEL_NAME).encode([chunk.text for chunk in chunks])
    store = VectorStore(VECTOR_STORE_DIR)
    store.build(vectors, chunks)
    store.save()
    return len(chunks)


if __name__ == "__main__":
    print(f"Indexed {ingest()} document chunks.")