"""Load and clean PDF and text documents while preserving source metadata."""

from dataclasses import dataclass
import logging
import re
from pathlib import Path

import fitz

from .security import find_injection_markers


logger = logging.getLogger(__name__)


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


def _is_safe_page(text: str, source: str, page: int) -> bool:
    """Quarantine pages that carry instructions aimed at the LLM."""
    markers = find_injection_markers(text)
    if markers:
        logger.warning("Quarantined %s page %d, injection markers: %s", source, page, markers)
        return False
    return True


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


def is_within_directory(path: Path, base_dir: Path) -> bool:
    """True when ``path`` (after resolving symlinks and ``..``) lies inside ``base_dir``."""
    return path.resolve().is_relative_to(base_dir.resolve())


def load_pdf_pages(documents_dir: Path) -> list[PageDocument]:
    """Extract non-empty pages from PDFs and text files below crop directories."""
    pages: list[PageDocument] = []
    document_paths = sorted(
        path
        for pattern in ("*/*.pdf", "*/*.txt")
        for path in documents_dir.glob(pattern)
    )
    for document_path in document_paths:
        # A symlink or junction could otherwise pull files from outside the
        # knowledge base (e.g. backend/.env) into the vector index.
        if not is_within_directory(document_path, documents_dir):
            logger.warning("Skipping document outside knowledge base: %s", document_path)
            continue
        crop = document_path.parent.name.lower()
        topic = topic_from_filename(document_path.name)
        if document_path.suffix.lower() == ".txt":
            text = clean_text(document_path.read_text(encoding="utf-8"))
            if text and _is_safe_page(text, document_path.name, 1):
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
                if text and _is_safe_page(text, document_path.name, page_number):
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