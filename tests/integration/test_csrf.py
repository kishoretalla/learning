"""
Integration tests for CSRF protection middleware.
The middleware is only active when ENVIRONMENT=production.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

VALID_NB_BODY = {
    "abstract": "x", "methodologies": [], "algorithms": [],
    "datasets": [], "results": "x", "conclusions": "x",
}


# ── Active in production ─────────────────────────────────────────────────────

def test_csrf_blocks_post_without_header_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    r = client.post("/api/generate-notebook", json=VALID_NB_BODY)
    assert r.status_code == 403
    assert "CSRF" in r.json()["detail"]


def test_csrf_blocks_put_without_header_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    r = client.put("/non-existent", json={})
    assert r.status_code == 403


def test_csrf_allows_post_with_fetch_header(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    r = client.post(
        "/api/generate-notebook",
        json=VALID_NB_BODY,
        headers={"X-Requested-With": "fetch"},
    )
    assert r.status_code != 403


def test_csrf_allows_post_with_xmlhttprequest_header(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    r = client.post(
        "/api/generate-notebook",
        json=VALID_NB_BODY,
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert r.status_code != 403


def test_csrf_allows_get_without_header_in_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    r = client.get("/health")
    assert r.status_code == 200


# ── Inactive outside production ──────────────────────────────────────────────

def test_csrf_not_enforced_in_development(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    r = client.post("/api/generate-notebook", json=VALID_NB_BODY)
    assert r.status_code != 403


def test_csrf_not_enforced_when_env_not_set(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    r = client.post("/api/generate-notebook", json=VALID_NB_BODY)
    assert r.status_code != 403
