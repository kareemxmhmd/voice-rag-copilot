"""Unit and integration tests for FastAPI endpoints."""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs_url" in data


def test_health_check_endpoint():
    """Verify health check returns status ok and vector count."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["vector_count"] == 81
    assert data["collection_name"] == "ecommerce_knowledge_base"


def test_ask_text_endpoint():
    """Verify ask-text endpoint answers query and provides latencies."""
    payload = {
        "query": "What is the list price of the Work Anywhere Bundle for Pro members?",
        "return_audio": True,
        "top_k": 3,
    }
    response = client.post("/ask-text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 10
    assert "sources" in data
    assert len(data["sources"]) > 0
    assert "latencies" in data
    assert data["latencies"]["retrieval_ms"] > 0
    assert data["latencies"]["llm_ms"] > 0
    assert data["audio_base64"] is not None


if __name__ == "__main__":
    test_root_endpoint()
    test_health_check_endpoint()
    test_ask_text_endpoint()
    print("All FastAPI endpoint tests passed!")
