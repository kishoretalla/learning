"""
Integration tests for GET /api/metrics and analytics instrumentation.
"""
import io
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app, _metrics

client = TestClient(app)

VALID_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
    b"/Contents 4 0 R /Resources << /Font << /F1 << /Type /Font "
    b"/Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\nendobj\n"
    b"4 0 obj\n<< /Length 44 >>\nstream\n"
    b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
    b"endstream\nendobj\n"
    b"xref\n0 5\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000274 00000 n \n"
    b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n370\n%%EOF"
)

VALID_ANALYSIS = {
    "abstract": "Test", "methodologies": [], "algorithms": [],
    "datasets": [], "results": "Good", "conclusions": "Done",
}


def _reset_metrics():
    """Reset metrics counters between tests."""
    for f in ("uploads_attempted", "upload_errors", "analyses_attempted",
              "analyses_successful", "api_key_invalid", "rate_limit_hits",
              "notebooks_generated", "colab_links_created"):
        setattr(_metrics, f, 0)


def test_metrics_endpoint_returns_200():
    r = client.get("/api/metrics")
    assert r.status_code == 200


def test_metrics_response_has_required_keys():
    r = client.get("/api/metrics")
    body = r.json()
    required = [
        "uploads_attempted", "upload_errors", "upload_error_rate",
        "analyses_attempted", "analyses_successful", "conversion_success_rate",
        "api_key_invalid", "rate_limit_hits",
        "notebooks_generated", "colab_links_created", "uptime_since",
    ]
    for key in required:
        assert key in body, f"Missing key: {key}"


def test_uploads_attempted_increments_on_valid_upload():
    _reset_metrics()
    before = _metrics.uploads_attempted
    client.post(
        "/api/extract-text",
        files={"file": ("p.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
        data={"api_key": "sk-test"},
    )
    assert _metrics.uploads_attempted == before + 1


def test_upload_errors_increments_on_bad_extension():
    _reset_metrics()
    client.post(
        "/api/extract-text",
        files={"file": ("p.txt", io.BytesIO(b"not a pdf"), "text/plain")},
        data={"api_key": "sk-test"},
    )
    assert _metrics.upload_errors == 1


def test_upload_errors_increments_on_empty_file():
    _reset_metrics()
    client.post(
        "/api/extract-text",
        files={"file": ("p.pdf", io.BytesIO(b""), "application/pdf")},
        data={"api_key": "sk-test"},
    )
    assert _metrics.upload_errors == 1


def test_analyses_attempted_increments():
    _reset_metrics()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({"abstract": "x", "methodologies": [],
                                   "algorithms": [], "datasets": [],
                                   "results": "x", "conclusions": "x"})
    mock_choice = MagicMock()
    mock_choice.message = mock_msg
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_resp

    with patch("backend.main.OpenAI", return_value=mock_client):
        client.post("/api/analyze-paper", json={"text": "some text", "api_key": "sk-t"})

    assert _metrics.analyses_attempted == 1
    assert _metrics.analyses_successful == 1


def test_api_key_invalid_increments_on_401():
    from openai import AuthenticationError
    _reset_metrics()
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = AuthenticationError(
        "bad key", response=MagicMock(status_code=401), body={}
    )
    with patch("backend.main.OpenAI", return_value=mock_client):
        client.post("/api/analyze-paper", json={"text": "x", "api_key": "sk-bad"})

    assert _metrics.api_key_invalid == 1


def test_rate_limit_hits_increments_on_429():
    from openai import RateLimitError
    _reset_metrics()
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RateLimitError(
        "rate limit", response=MagicMock(status_code=429), body={}
    )
    with patch("backend.main.OpenAI", return_value=mock_client):
        client.post("/api/analyze-paper", json={"text": "x", "api_key": "sk-t"})

    assert _metrics.rate_limit_hits == 1


def test_notebooks_generated_increments():
    _reset_metrics()
    client.post("/api/generate-notebook", json=VALID_ANALYSIS)
    assert _metrics.notebooks_generated == 1


def test_conversion_success_rate_is_zero_when_no_analyses():
    _reset_metrics()
    r = client.get("/api/metrics")
    assert r.json()["conversion_success_rate"] == 0.0


def test_conversion_success_rate_computed_correctly():
    _reset_metrics()
    _metrics.analyses_attempted = 4
    _metrics.analyses_successful = 3
    r = client.get("/api/metrics")
    assert r.json()["conversion_success_rate"] == 0.75


def test_upload_error_rate_computed_correctly():
    _reset_metrics()
    _metrics.uploads_attempted = 10
    _metrics.upload_errors = 2
    r = client.get("/api/metrics")
    assert r.json()["upload_error_rate"] == 0.2


def test_uptime_since_is_iso_timestamp():
    r = client.get("/api/metrics")
    uptime = r.json()["uptime_since"]
    from datetime import datetime, timezone
    # Should parse without error
    datetime.fromisoformat(uptime)
