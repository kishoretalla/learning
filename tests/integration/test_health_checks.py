"""
Integration tests for health check endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_frontend_health_check():
    """Test that the frontend /api/health endpoint responds when the frontend is running."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=3.0) as http:
            response = await http.get("http://localhost:3000/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "research-notebook-frontend" in data["service"]
    except (httpx.ConnectError, httpx.TimeoutException):
        pytest.skip("Frontend not running — skipping live health check")


@pytest.mark.asyncio
async def test_backend_health_check():
    """Test that backend FastAPI health check endpoint responds"""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "research-notebook-backend" in response.json()["service"]


@pytest.mark.asyncio
async def test_backend_root_endpoint():
    """Test that backend root endpoint is accessible"""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Research Notebook Backend" in response.json()["message"]
