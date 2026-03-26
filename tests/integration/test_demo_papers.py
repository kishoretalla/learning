"""
Integration tests for Task 11 — Demo Papers Library.
GET /api/demo-papers  and  POST /api/demo-papers/{id}/extract
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.demo_papers import DEMO_PAPERS

client = TestClient(app)


def test_list_demo_papers_returns_200():
    r = client.get("/api/demo-papers")
    assert r.status_code == 200


def test_list_returns_correct_count():
    r = client.get("/api/demo-papers")
    assert len(r.json()) == len(DEMO_PAPERS)


def test_list_items_have_required_fields():
    r = client.get("/api/demo-papers")
    for item in r.json():
        assert "id" in item
        assert "title" in item
        assert "description" in item
        assert "topic" in item
        assert "year" in item


def test_list_does_not_expose_text():
    r = client.get("/api/demo-papers")
    for item in r.json():
        assert "text" not in item


def test_extract_known_paper_returns_200():
    paper_id = DEMO_PAPERS[0]["id"]
    r = client.post(f"/api/demo-papers/{paper_id}/extract")
    assert r.status_code == 200


def test_extract_returns_structured_response():
    paper_id = DEMO_PAPERS[0]["id"]
    r = client.post(f"/api/demo-papers/{paper_id}/extract")
    body = r.json()
    assert "filename" in body
    assert "total_pages" in body
    assert "total_chars" in body
    assert "pages" in body
    assert isinstance(body["pages"], list)
    assert len(body["pages"]) > 0


def test_extract_marks_is_demo_true():
    paper_id = DEMO_PAPERS[0]["id"]
    r = client.post(f"/api/demo-papers/{paper_id}/extract")
    assert r.json()["is_demo"] is True


def test_extract_includes_title():
    paper = DEMO_PAPERS[0]
    r = client.post(f"/api/demo-papers/{paper['id']}/extract")
    assert r.json()["title"] == paper["title"]


def test_extract_pages_have_text():
    paper_id = DEMO_PAPERS[0]["id"]
    r = client.post(f"/api/demo-papers/{paper_id}/extract")
    for page in r.json()["pages"]:
        assert "page_number" in page
        assert "text" in page
        assert "char_count" in page
        assert page["char_count"] == len(page["text"])


def test_extract_unknown_paper_returns_404():
    r = client.post("/api/demo-papers/does-not-exist/extract")
    assert r.status_code == 404


def test_all_demo_papers_are_extractable():
    for paper in DEMO_PAPERS:
        r = client.post(f"/api/demo-papers/{paper['id']}/extract")
        assert r.status_code == 200, f"Failed for {paper['id']}"


def test_total_chars_matches_sum_of_pages():
    paper_id = DEMO_PAPERS[0]["id"]
    r = client.post(f"/api/demo-papers/{paper_id}/extract")
    body = r.json()
    assert body["total_chars"] == sum(p["char_count"] for p in body["pages"])
