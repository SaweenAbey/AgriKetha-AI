"""Split extracted pages into searchable chunks."""

from dataclasses import dataclass

from .document_loader import PageDocument


@dataclass(frozen=True)
class DocumentChunk:
    text: str
    source: str
    page: int
    crop: str
    topic: str


def chunk_pages(
    pages: list[PageDocument], chunk_size: int = 180, overlap: int = 30
) -> list[DocumentChunk]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    chunks: list[DocumentChunk] = []
    step = chunk_size - overlap
    for page in pages:
        words = page.text.split()
        for start in range(0, len(words), step):
            text = " ".join(words[start : start + chunk_size])
            if text:
                chunks.append(
                    DocumentChunk(
                        text=text,
                        source=page.source,
                        page=page.page,
                        crop=page.crop,
                        topic=page.topic,
                    )
                )
            if start + chunk_size >= len(words):
                break
    return chunks