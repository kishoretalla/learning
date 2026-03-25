"""
Integration tests for health check endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_frontend_health_check():
    """Test that frontend health check endpoint responds"""
    from frontend.app.api.health.route import GET
    
    response = await GET()
    assert response.status_code == 200
    assert response.body
    data = response.body
    # Since it's a JSONResponse, we need to parse it
    import json
    parsed = json.loads(data)
    assert parsed["status"] == "ok"
    assert "research-notebook-frontend" in parsed["service"]


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
