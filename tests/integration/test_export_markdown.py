"""
Integration tests for Task 12 — Markdown Export.
POST /api/export-markdown
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

VALID_ANALYSIS = {
    "abstract": "A novel GPT-4o approach to ARC tasks.",
    "methodologies": ["few-shot prompting", "chain-of-thought"],
    "algorithms": ["beam search", "GPT-4o"],
    "datasets": ["ARC-AGI benchmark"],
    "results": "Achieved 85% accuracy.",
    "conclusions": "LLMs can solve abstract reasoning.",
    "filename": "arc-paper.pdf",
}


def test_returns_200():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert r.status_code == 200


def test_content_type_is_markdown():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "text/markdown" in r.headers["content-type"]


def test_content_disposition_is_md_file():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    cd = r.headers["content-disposition"]
    assert "attachment" in cd
    assert ".md" in cd


def test_filename_derived_from_input():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "arc-paper-notebook.md" in r.headers["content-disposition"]


def test_default_filename_when_none():
    body = {**VALID_ANALYSIS, "filename": None}
    r = client.post("/api/export-markdown", json=body)
    assert "paper-notebook.md" in r.headers["content-disposition"]


def test_contains_title_heading():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "# arc-paper" in r.text


def test_contains_abstract():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "## Abstract" in r.text
    assert "GPT-4o approach" in r.text


def test_contains_methodologies():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "## Key Methodologies" in r.text
    assert "few-shot prompting" in r.text
    assert "chain-of-thought" in r.text


def test_contains_algorithms_with_code_fences():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "## Algorithms" in r.text
    assert "```python" in r.text
    assert "beam_search" in r.text
    assert "NotImplementedError" in r.text


def test_contains_datasets():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "## Datasets" in r.text
    assert "ARC-AGI benchmark" in r.text


def test_contains_results():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "## Results" in r.text
    assert "85%" in r.text


def test_contains_conclusions():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "## Conclusions" in r.text
    assert "abstract reasoning" in r.text


def test_contains_references():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "## References" in r.text


def test_github_ready_section_dividers():
    r = client.post("/api/export-markdown", json=VALID_ANALYSIS)
    assert "---" in r.text


def test_rejects_empty_analysis():
    body = {**VALID_ANALYSIS, "abstract": "", "results": ""}
    r = client.post("/api/export-markdown", json=body)
    assert r.status_code == 400


def test_missing_required_field_returns_422():
    body = {k: v for k, v in VALID_ANALYSIS.items() if k != "abstract"}
    r = client.post("/api/export-markdown", json=body)
    assert r.status_code == 422


def test_empty_algorithms_produces_valid_markdown():
    body = {**VALID_ANALYSIS, "algorithms": []}
    r = client.post("/api/export-markdown", json=body)
    assert r.status_code == 200
    assert "## Algorithms" in r.text


def test_empty_datasets_produces_valid_markdown():
    body = {**VALID_ANALYSIS, "datasets": []}
    r = client.post("/api/export-markdown", json=body)
    assert r.status_code == 200
