"""
Integration tests for POST /api/analyze-paper
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from google.genai import errors as genai_errors

from backend.main import app

client = TestClient(app)

SAMPLE_TEXT = "This paper presents a novel approach to solving ARC tasks using Gemini. " * 50

MOCK_ANALYSIS = {
    "abstract": "A novel approach using Gemini for ARC tasks.",
    "methodologies": ["few-shot prompting", "chain-of-thought"],
    "algorithms": ["Gemini", "beam search"],
    "datasets": ["ARC-AGI benchmark"],
    "results": "Achieved 85% on ARC public eval.",
    "conclusions": "LLMs can solve abstract reasoning tasks with careful prompting.",
}


def _mock_gemini(response_json: dict):
    """Return a patch context that makes genai.Client().models.generate_content() return response_json."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(response_json)

    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response

    mock_client = MagicMock()
    mock_client.models = mock_models

    return patch("backend.main.genai.Client", return_value=mock_client)


def test_analyze_paper_returns_structured_json():
    with _mock_gemini(MOCK_ANALYSIS):
        r = client.post("/api/analyze-paper", json={"text": SAMPLE_TEXT, "api_key": "AIza-test"})

    assert r.status_code == 200
    body = r.json()
    assert "abstract" in body
    assert "methodologies" in body
    assert "algorithms" in body
    assert "datasets" in body
    assert "results" in body
    assert "conclusions" in body


def test_analyze_paper_returns_correct_values():
    with _mock_gemini(MOCK_ANALYSIS):
        r = client.post("/api/analyze-paper", json={"text": SAMPLE_TEXT, "api_key": "AIza-test"})

    body = r.json()
    assert body["abstract"] == MOCK_ANALYSIS["abstract"]
    assert body["methodologies"] == MOCK_ANALYSIS["methodologies"]
    assert body["datasets"] == MOCK_ANALYSIS["datasets"]


def test_analyze_paper_with_filename():
    with _mock_gemini(MOCK_ANALYSIS):
        r = client.post(
            "/api/analyze-paper",
            json={"text": SAMPLE_TEXT, "api_key": "AIza-test", "filename": "arc-paper.pdf"},
        )
    assert r.status_code == 200


def test_rejects_empty_text():
    r = client.post("/api/analyze-paper", json={"text": "", "api_key": "AIza-test"})
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


def test_rejects_whitespace_only_text():
    r = client.post("/api/analyze-paper", json={"text": "   \n\t  ", "api_key": "AIza-test"})
    assert r.status_code == 400


def test_rejects_empty_api_key():
    r = client.post("/api/analyze-paper", json={"text": SAMPLE_TEXT, "api_key": ""})
    assert r.status_code == 400
    assert "API key" in r.json()["detail"]


def _make_client_error(status: str, code: int = 400) -> genai_errors.ClientError:
    return genai_errors.ClientError(code, {"status": status, "error": {"message": status}})


def test_invalid_api_key_returns_401():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = _make_client_error("PERMISSION_DENIED", 403)
    with patch("backend.main.genai.Client", return_value=mock_client):
        r = client.post("/api/analyze-paper", json={"text": SAMPLE_TEXT, "api_key": "bad-key"})

    assert r.status_code == 401
    assert "Invalid Gemini API key" in r.json()["detail"]


def test_rate_limit_returns_429():
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = _make_client_error("RESOURCE_EXHAUSTED", 429)
    with patch("backend.main.genai.Client", return_value=mock_client):
        r = client.post("/api/analyze-paper", json={"text": SAMPLE_TEXT, "api_key": "AIza-test"})

    assert r.status_code == 429
    assert "rate limit" in r.json()["detail"].lower()


def test_text_is_truncated_to_100k_chars():
    """Verify that oversized text is truncated rather than rejected."""
    long_text = "word " * 30_000  # ~150k chars

    captured_calls = {}

    def capture_generate(model, contents, config):
        captured_calls["contents"] = contents
        mock_response = MagicMock()
        mock_response.text = json.dumps(MOCK_ANALYSIS)
        return mock_response

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = capture_generate

    with patch("backend.main.genai.Client", return_value=mock_client):
        r = client.post("/api/analyze-paper", json={"text": long_text, "api_key": "AIza-test"})

    assert r.status_code == 200
    # The contents string includes system prompt + paper text; paper portion must be ≤100k chars
    assert len(captured_calls["contents"]) <= 100_000 + 1_000  # headroom for system prompt prefix


def test_missing_text_field_returns_422():
    r = client.post("/api/analyze-paper", json={"api_key": "AIza-test"})
    assert r.status_code == 422


def test_missing_api_key_field_returns_422():
    r = client.post("/api/analyze-paper", json={"text": SAMPLE_TEXT})
    assert r.status_code == 422
