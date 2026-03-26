"""
Integration tests for POST /api/create-colab-link
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

SAMPLE_NB = json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5})


def _mock_github(username: str = "testuser", gist_id: str = "abc123def456"):
    """Patch httpx.AsyncClient to return mock GitHub API responses."""
    mock_client = AsyncMock()

    user_response = MagicMock()
    user_response.status_code = 200
    user_response.json.return_value = {"login": username}

    gist_response = MagicMock()
    gist_response.status_code = 201
    gist_response.json.return_value = {"id": gist_id}

    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=user_response)
    mock_client.post = AsyncMock(return_value=gist_response)

    return patch("backend.main.httpx.AsyncClient", return_value=mock_client)


# ── No token ────────────────────────────────────────────────────────────────

def test_returns_unavailable_when_no_github_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    r = client.post("/api/create-colab-link", json={"notebook_json": SAMPLE_NB})
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is False
    assert "reason" in body


# ── Happy path ───────────────────────────────────────────────────────────────

def test_returns_colab_url_when_token_set(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp-fake-token")
    with _mock_github("researchuser", "gist99"):
        r = client.post(
            "/api/create-colab-link",
            json={"notebook_json": SAMPLE_NB, "filename": "my-paper-notebook.ipynb"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is True
    assert "colab_url" in body
    assert "colab.research.google.com" in body["colab_url"]
    assert "gist_url" in body
    assert "gist_id" in body


def test_colab_url_contains_username_and_gist_id(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp-fake-token")
    with _mock_github("alice", "gist123"):
        r = client.post("/api/create-colab-link", json={"notebook_json": SAMPLE_NB})
    body = r.json()
    assert "alice" in body["colab_url"]
    assert "gist123" in body["colab_url"]


def test_gist_url_contains_gist_id(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp-fake-token")
    with _mock_github("bob", "xyz789"):
        r = client.post("/api/create-colab-link", json={"notebook_json": SAMPLE_NB})
    assert "xyz789" in r.json()["gist_url"]


def test_filename_appended_with_ipynb_if_missing(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp-fake-token")
    with _mock_github() as mock_ctx:
        r = client.post(
            "/api/create-colab-link",
            json={"notebook_json": SAMPLE_NB, "filename": "my-notebook"},
        )
    assert r.status_code == 200
    # The gist post was called with a .ipynb filename
    mock_instance = mock_ctx.return_value
    call_kwargs = mock_instance.post.call_args.kwargs
    files = call_kwargs["json"]["files"]
    assert any(k.endswith(".ipynb") for k in files)


# ── Error cases ──────────────────────────────────────────────────────────────

def test_returns_unavailable_on_bad_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp-bad")

    mock_client = AsyncMock()
    bad_user = MagicMock()
    bad_user.status_code = 401
    bad_user.json.return_value = {"message": "Bad credentials"}
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=bad_user)

    with patch("backend.main.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/api/create-colab-link", json={"notebook_json": SAMPLE_NB})

    assert r.status_code == 200
    assert r.json()["available"] is False


def test_returns_unavailable_on_gist_creation_failure(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp-fake")

    mock_client = AsyncMock()
    user_ok = MagicMock(status_code=200)
    user_ok.json.return_value = {"login": "user"}
    gist_fail = MagicMock(status_code=422)
    gist_fail.json.return_value = {"message": "Validation Failed"}
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=user_ok)
    mock_client.post = AsyncMock(return_value=gist_fail)

    with patch("backend.main.httpx.AsyncClient", return_value=mock_client):
        r = client.post("/api/create-colab-link", json={"notebook_json": SAMPLE_NB})

    assert r.status_code == 200
    assert r.json()["available"] is False


def test_rejects_empty_notebook_json(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp-fake")
    r = client.post("/api/create-colab-link", json={"notebook_json": ""})
    assert r.status_code == 400


def test_missing_notebook_json_returns_422():
    r = client.post("/api/create-colab-link", json={})
    assert r.status_code == 422


def test_notebook_has_colab_metadata():
    """Ensure _build_notebook adds colab metadata (checked via generate-notebook)."""
    import nbformat
    from backend.main import GenerateNotebookRequest, _build_notebook

    req = GenerateNotebookRequest(
        abstract="Test abstract",
        methodologies=["method1"],
        algorithms=["algo1"],
        datasets=["dataset1"],
        results="Good results",
        conclusions="Strong conclusions",
        filename="test-paper.pdf",
    )
    nb = _build_notebook(req)
    assert "colab" in nb.metadata
    assert "name" in nb.metadata["colab"]
    assert nb.metadata["colab"]["name"].endswith(".ipynb")


def test_setup_cell_uses_try_except_import():
    """Ensure setup cell handles missing packages gracefully (Colab-compatible)."""
    from backend.main import GenerateNotebookRequest, _build_notebook

    req = GenerateNotebookRequest(
        abstract="x", methodologies=[], algorithms=[], datasets=[],
        results="x", conclusions="x",
    )
    nb = _build_notebook(req)
    code_cells = [c.source for c in nb.cells if c.cell_type == "code"]
    setup = code_cells[0]
    assert "try:" in setup
    assert "ImportError" in setup
    assert "subprocess" in setup
