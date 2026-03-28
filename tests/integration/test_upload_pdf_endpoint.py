"""
Integration tests for the upload PDF -> analyze paper flow with mocked Gemini.
"""
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app
from tests.integration.test_extract_text import VALID_PDF

client = TestClient(app)

MOCK_ANALYSIS = {
    "abstract": "Attention-only models can replace recurrence for sequence modeling.",
    "methodologies": ["self-attention", "multi-head attention"],
    "algorithms": ["Scaled Dot-Product Attention"],
    "datasets": ["WMT 2014 English-German"],
    "results": "Transformer improves BLEU while training faster.",
    "conclusions": "Parallel attention architectures are effective for translation.",
}


def _mock_gemini(response_json: dict):
    mock_response = MagicMock()
    mock_response.text = json.dumps(response_json)

    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response

    mock_client = MagicMock()
    mock_client.models = mock_models
    return patch("backend.main.genai.Client", return_value=mock_client)


def test_upload_pdf_flow_returns_mocked_analysis_contract():
    extract_response = client.post(
        "/api/extract-text",
        files={"file": ("attention.pdf", VALID_PDF, "application/pdf")},
        data={"api_key": "AIza-test"},
    )

    assert extract_response.status_code == 200
    extracted = extract_response.json()
    paper_text = "\n".join(page["text"] for page in extracted["pages"])

    with _mock_gemini(MOCK_ANALYSIS):
        analyze_response = client.post(
            "/api/analyze-paper",
            json={
                "text": paper_text,
                "api_key": "AIza-test",
                "filename": extracted["filename"],
            },
        )

    assert analyze_response.status_code == 200
    body = analyze_response.json()
    assert body == MOCK_ANALYSIS
    assert extracted["filename"] == "attention.pdf"
    assert extracted["total_pages"] >= 1