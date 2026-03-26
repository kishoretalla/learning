"""
Integration tests for POST /api/generate-notebook
"""
import json

import nbformat
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

VALID_ANALYSIS = {
    "abstract": "This paper presents a novel approach to ARC tasks using GPT-4o.",
    "methodologies": ["few-shot prompting", "chain-of-thought reasoning"],
    "algorithms": ["beam search", "GPT-4o"],
    "datasets": ["ARC-AGI benchmark", "synthetic grid tasks"],
    "results": "Achieved 85% accuracy on ARC public eval, outperforming prior SOTA by 12%.",
    "conclusions": "LLMs with careful prompting can solve abstract reasoning tasks effectively.",
    "filename": "arc-paper.pdf",
}


def _post(body: dict) -> "Response":
    return client.post("/api/generate-notebook", json=body)


def test_returns_octet_stream():
    r = _post(VALID_ANALYSIS)
    assert r.status_code == 200
    assert "application/octet-stream" in r.headers["content-type"]


def test_content_disposition_has_ipynb_filename():
    r = _post(VALID_ANALYSIS)
    assert r.status_code == 200
    cd = r.headers["content-disposition"]
    assert ".ipynb" in cd
    assert "attachment" in cd


def test_filename_derived_from_input():
    r = _post(VALID_ANALYSIS)
    cd = r.headers["content-disposition"]
    assert "arc-paper-notebook.ipynb" in cd


def test_default_filename_when_none_provided():
    body = {**VALID_ANALYSIS, "filename": None}
    r = _post(body)
    assert r.status_code == 200
    assert "paper-notebook.ipynb" in r.headers["content-disposition"]


def test_response_is_valid_ipynb():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    nbformat.validate(nb)  # raises if invalid


def test_notebook_has_markdown_and_code_cells():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    cell_types = {c.cell_type for c in nb.cells}
    assert "markdown" in cell_types
    assert "code" in cell_types


def test_notebook_contains_abstract():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    all_text = " ".join(c.source for c in nb.cells)
    assert "novel approach to ARC tasks" in all_text


def test_notebook_contains_methodologies():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    all_text = " ".join(c.source for c in nb.cells)
    assert "few-shot prompting" in all_text
    assert "chain-of-thought reasoning" in all_text


def test_notebook_contains_algorithm_stubs():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    code_cells = [c.source for c in nb.cells if c.cell_type == "code"]
    combined = "\n".join(code_cells)
    assert "beam_search" in combined
    assert "def " in combined
    assert "NotImplementedError" in combined


def test_notebook_contains_datasets():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    all_text = " ".join(c.source for c in nb.cells)
    assert "ARC-AGI benchmark" in all_text


def test_notebook_contains_results():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    all_text = " ".join(c.source for c in nb.cells)
    assert "85%" in all_text


def test_notebook_contains_conclusions():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    all_text = " ".join(c.source for c in nb.cells)
    assert "abstract reasoning" in all_text


def test_notebook_has_kernelspec_metadata():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    assert nb.metadata["kernelspec"]["language"] == "python"


def test_notebook_has_setup_cell_with_imports():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    code_cells = [c.source for c in nb.cells if c.cell_type == "code"]
    setup = code_cells[0]  # first code cell is setup
    assert "import numpy" in setup
    assert "import pandas" in setup
    assert "import matplotlib" in setup


def test_one_algo_stub_per_algorithm():
    r = _post(VALID_ANALYSIS)
    nb = nbformat.reads(r.text, as_version=4)
    code_cells = [c.source for c in nb.cells if c.cell_type == "code"]
    stub_cells = [c for c in code_cells if "NotImplementedError" in c]
    assert len(stub_cells) == len(VALID_ANALYSIS["algorithms"])


def test_rejects_fully_empty_analysis():
    body = {
        **VALID_ANALYSIS,
        "abstract": "",
        "results": "",
    }
    r = _post(body)
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


def test_missing_required_field_returns_422():
    body = {k: v for k, v in VALID_ANALYSIS.items() if k != "abstract"}
    r = _post(body)
    assert r.status_code == 422


def test_empty_algorithms_list_produces_valid_notebook():
    body = {**VALID_ANALYSIS, "algorithms": []}
    r = _post(body)
    assert r.status_code == 200
    nb = nbformat.reads(r.text, as_version=4)
    nbformat.validate(nb)


def test_empty_datasets_list_produces_valid_notebook():
    body = {**VALID_ANALYSIS, "datasets": []}
    r = _post(body)
    assert r.status_code == 200
    nbformat.validate(nbformat.reads(r.text, as_version=4))
