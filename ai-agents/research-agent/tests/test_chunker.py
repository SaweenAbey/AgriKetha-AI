from app.chunker import chunk_pages
from app.document_loader import PageDocument, clean_text, topic_from_filename


def test_clean_text_and_filename_topic():
    assert clean_text("Early\n blight  causes spots") == "Early blight causes spots"
    assert topic_from_filename("tomato_disease_guide.pdf") == "disease"


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