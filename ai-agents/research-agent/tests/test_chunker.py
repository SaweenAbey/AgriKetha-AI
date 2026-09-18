from pathlib import Path

from app.chunker import chunk_pages
from app.document_loader import (
    PageDocument,
    clean_text,
    load_pdf_pages,
    topic_from_filename,
)


def test_clean_text_and_filename_topic():
    assert clean_text("Early\n blight  causes spots") == "Early blight causes spots"
    assert topic_from_filename("tomato_disease_guide.pdf") == "disease"


def test_loads_non_empty_text_files(tmp_path: Path):
    text_file = tmp_path / "rice"
    text_file.mkdir()
    (text_file / "rice_irrigation.txt").write_text(
        "Water the crop regularly.", encoding="utf-8"
    )

    pages = load_pdf_pages(tmp_path)

    assert pages == [
        PageDocument(
            text="Water the crop regularly.",
            source="rice_irrigation.txt",
            page=1,
            crop="rice",
            topic="irrigation",
        )
    ]


def test_chunking_preserves_page_metadata():
    page = PageDocument(
        text="one two three four five",
        source="guide.pdf",
        page=4,
        crop="tomato",
        topic="disease",
    )
    chunks = chunk_pages([page], chunk_size=3, overlap=1)
    assert [chunk.text for chunk in chunks] == ["one two three", "three four five"]
    assert chunks[0].source == "guide.pdf"
    assert chunks[0].page == 4