"""
Integration tests for Task 1: Backend persistence and auth dependencies.

Verifies:
1. Auth and DB dependencies are installed and importable
2. Database connection can be initialized
3. FastAPI app boots cleanly with DB middleware
"""
import os
import tempfile
import pytest
from pathlib import Path


def test_auth_dependencies_importable():
    """Verify auth libraries are installed and importable."""
    try:
        import sqlmodel
        import passlib
        import bcrypt
        from jose import jwt
    except ImportError as e:
        pytest.fail(f"Auth dependency missing: {e}")


def test_db_module_exists_and_importable():
    """Verify backend/db.py module exists and imports cleanly."""
    try:
        from backend import db
        assert hasattr(db, 'get_db')
        assert hasattr(db, 'init_db')
    except ImportError as e:
        pytest.fail(f"backend.db module not found or not importable: {e}")


def test_fastapi_app_boots_with_db():
    """Verify the FastAPI app initializes without errors when DB is configured."""
    from backend.main import app
    # If this imports and calls app(), the app bootstrapping is clean
    assert app is not None
    assert app.title == "Research Notebook Backend"
    # Check that app has expected routes from v1
    route_paths = {route.path for route in app.routes}
    assert "/health" in route_paths
    assert "/api/metrics" in route_paths


def test_db_initializes_with_temp_sqlite():
    """Verify the database module can initialize with a temporary SQLite."""
    from backend.db import init_db, get_session_factory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        db_url = f"sqlite:///{test_db_path}"
        
        # Should initialize without errors
        engine = init_db(db_url)
        assert engine is not None
        
        # Should be able to create a session factory
        session_factory = get_session_factory(engine)
        assert session_factory is not None
        
        # Database file should exist after initialization
        assert test_db_path.exists()


@pytest.mark.asyncio
async def test_fastapi_health_still_works():
    """Verify v1 endpoints like /health still work after DB setup."""
    from fastapi.testclient import TestClient
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "research-notebook-backend"
