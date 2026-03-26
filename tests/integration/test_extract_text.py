"""
Integration tests for POST /api/extract-text
"""
import io

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

# Minimal valid PDF bytes
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


def _upload(filename: str, content: bytes, api_key: str = "sk-test") -> dict:
    return client.post(
        "/api/extract-text",
        files={"file": (filename, io.BytesIO(content), "application/pdf")},
        data={"api_key": api_key},
    )


def test_valid_pdf_returns_structured_response():
    r = _upload("paper.pdf", VALID_PDF)
    assert r.status_code == 200
    body = r.json()
    assert body["filename"] == "paper.pdf"
    assert body["total_pages"] >= 1
    assert isinstance(body["total_chars"], int)
    assert isinstance(body["pages"], list)
    page = body["pages"][0]
    assert page["page_number"] == 1
    assert "text" in page
    assert "char_count" in page


def test_page_char_count_matches_text_length():
    r = _upload("paper.pdf", VALID_PDF)
    assert r.status_code == 200
    for page in r.json()["pages"]:
        assert page["char_count"] == len(page["text"])


def test_total_chars_is_sum_of_pages():
    r = _upload("paper.pdf", VALID_PDF)
    assert r.status_code == 200
    body = r.json()
    assert body["total_chars"] == sum(p["char_count"] for p in body["pages"])


def test_rejects_non_pdf_filename():
    r = _upload("paper.txt", VALID_PDF)
    assert r.status_code == 400
    assert "PDF" in r.json()["detail"]


def test_rejects_empty_file():
    r = _upload("empty.pdf", b"")
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


def test_rejects_file_without_pdf_magic_bytes():
    r = _upload("fake.pdf", b"This is not a PDF at all")
    assert r.status_code == 400
    assert "valid PDF" in r.json()["detail"]


def test_rejects_file_over_10mb():
    big = b"%PDF-1.4\n" + b"x" * (10 * 1024 * 1024 + 1)
    r = _upload("huge.pdf", big)
    assert r.status_code == 413
    assert "10 MB" in r.json()["detail"]


def test_requires_api_key_field():
    r = client.post(
        "/api/extract-text",
        files={"file": ("paper.pdf", io.BytesIO(VALID_PDF), "application/pdf")},
        # no api_key
    )
    assert r.status_code == 422  # FastAPI validation error


def test_response_contains_filename():
    r = _upload("my-research-paper.pdf", VALID_PDF)
    assert r.status_code == 200
    assert r.json()["filename"] == "my-research-paper.pdf"
