"""Load and clean PDF and text documents while preserving source metadata."""

from dataclasses import dataclass
import re
from pathlib import Path

import fitz


@dataclass(frozen=True)
class PageDocument:
    text: str
    source: str
    page: int
    crop: str
    topic: str


def clean_text(text: str) -> str:
    """Normalize PDF whitespace without changing the document's wording."""
    return re.sub(r"\s+", " ", text).strip()


def topic_from_filename(filename: str) -> str:
    """Use a recognizable topic token from the supplied filename when available."""
    stem = Path(filename).stem.lower()
    topics = (
        "planting",
        "care",
        "water",
        "irrigation",
        "fertilizer",
        "nutrient",
        "pest",
        "disease",
        "harvest",
        "machinery",
    )
    return next((topic for topic in topics if topic in stem), "general")


def load_pdf_pages(documents_dir: Path) -> list[PageDocument]:
    """Extract non-empty pages from PDFs and text files below crop directories."""
    pages: list[PageDocument] = []
    document_paths = sorted(
        path
        for pattern in ("*/*.pdf", "*/*.txt")
        for path in documents_dir.glob(pattern)
    )
    for document_path in document_paths:
        crop = document_path.parent.name.lower()
        topic = topic_from_filename(document_path.name)
        if document_path.suffix.lower() == ".txt":
            text = clean_text(document_path.read_text(encoding="utf-8"))
            if text:
                pages.append(
                    PageDocument(
                        text=text,
                        source=document_path.name,
                        page=1,
                        crop=crop,
                        topic=topic,
                    )
                )
            continue

        with fitz.open(document_path) as document:
            for page_number, page in enumerate(document, start=1):
                text = clean_text(page.get_text())
                if text:
                    pages.append(
                        PageDocument(
                            text=text,
                            source=document_path.name,
                            page=page_number,
                            crop=crop,
                            topic=topic,
                        )
                    )
    return pages