"""
Integration tests for POST /api/arxiv-url
"""
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

MOCK_METADATA = {
    "id": "1706.03762v7",
    "title": "Attention Is All You Need",
    "summary": "We propose the Transformer, a new simple network architecture based solely on attention mechanisms.",
    "published": "2017-06-12T17:57:25Z",
    "authors": ["Ashish Vaswani", "Noam Shazeer"],
    "abs_url": "https://arxiv.org/abs/1706.03762v7",
    "pdf_url": "https://arxiv.org/pdf/1706.03762v7.pdf",
}

MOCK_ANALYSIS = {
    "abstract": "Transformer replaces recurrence with attention.",
    "methodologies": ["self-attention"],
    "algorithms": ["multi-head attention"],
    "datasets": ["WMT 2014 English-German"],
    "results": "Improved BLEU with lower training cost.",
    "conclusions": "Attention-only architectures work well.",
}


def _mock_gemini(response_json: dict):
    mock_response = MagicMock()
    mock_response.text = json.dumps(response_json)

    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response

    mock_client = MagicMock()
    mock_client.models = mock_models

    return patch("backend.main.genai.Client", return_value=mock_client)


def test_arxiv_url_returns_extraction_payload_with_analysis():
    with patch("backend.main.fetch_arxiv_metadata", return_value=MOCK_METADATA):
        with _mock_gemini(MOCK_ANALYSIS):
            response = client.post(
                "/api/arxiv-url",
                json={"url": "https://arxiv.org/abs/1706.03762", "api_key": "AIza-test"},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "1706.03762v7.pdf"
    assert body["is_arxiv"] is True
    assert body["title"] == MOCK_METADATA["title"]
    assert body["analysis"] == MOCK_ANALYSIS
    assert body["pages"][0]["char_count"] == len(body["pages"][0]["text"])


def test_arxiv_url_rejects_invalid_identifier():
    response = client.post(
        "/api/arxiv-url",
        json={"url": "https://example.com/not-arxiv", "api_key": "AIza-test"},
    )

    assert response.status_code == 400
    assert "Invalid arXiv identifier" in response.json()["detail"]