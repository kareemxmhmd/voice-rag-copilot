"""Unit tests for chunking, retriever, and voice language detection."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import settings
from src.rag.ingest import parse_markdown_to_chunks
from src.rag.retriever import VoiceRetriever
from src.voice.tts import detect_language, get_default_voice_for_text


def test_markdown_chunking():
    """Verify that markdown parsing extracts non-empty chunks with hierarchy."""
    doc_path = settings.raw_data_dir / "01_subscription_plans.md"
    assert doc_path.exists(), f"Missing test file: {doc_path}"

    chunks = parse_markdown_to_chunks(doc_path)
    assert len(chunks) > 10
    first_chunk = chunks[0]
    assert first_chunk.source_file == "01_subscription_plans.md"
    assert len(first_chunk.content) > 50
    assert first_chunk.section != ""


def test_vector_store_indexed_count():
    """Verify that ChromaDB collection is populated with indexed chunks."""
    retriever = VoiceRetriever(top_k=3)
    count = retriever.collection.count()
    assert count == 81, f"Expected 81 chunks in vector store, found {count}"


def test_retriever_query():
    """Verify that retriever returns top_k results with similarity scores."""
    retriever = VoiceRetriever(top_k=3)
    results = retriever.retrieve("What is the refund policy for Pro plan?")
    assert len(results) == 3
    for r in results:
        assert "content" in r
        assert "source" in r
        assert 0.0 <= r["score"] <= 1.0


def test_language_detection():
    """Verify that Arabic and English texts are correctly identified."""
    assert detect_language("What is the Pro plan annual price?") == "en"
    assert detect_language("لو نسيت ألغي الاشتراك التجريبي هتدفعوني كام؟") == "ar"
    assert detect_language("أنا على Basic وعاوز أعمل Upgrade للـ Pro") == "ar"

    assert get_default_voice_for_text("Hello world") == "en-US-JennyNeural"
    assert get_default_voice_for_text("أهلاً بيك في نوفا كارت") == "ar-EG-SalmaNeural"


if __name__ == "__main__":
    test_markdown_chunking()
    test_vector_store_indexed_count()
    test_retriever_query()
    test_language_detection()
    print("All retriever unit tests passed!")
