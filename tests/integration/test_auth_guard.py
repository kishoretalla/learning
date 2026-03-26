"""Tests for Task 6: Backend auth guard utility for protected routes."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.models import User
from backend.auth import hash_password


@pytest.fixture
def client(app_with_db):
    """FastAPI test client."""
    return TestClient(app_with_db)


@pytest.fixture
def authenticated_user(session_with_db):
    """Create an authenticated test user."""
    user = User(
        email="guard@example.com",
        hashed_password=hash_password("GuardPassword123"),
        full_name="Guard Test User",
    )
    session_with_db.add(user)
    session_with_db.commit()
    session_with_db.refresh(user)
    return user


def test_protected_endpoint_requires_session(client, authenticated_user):
    """Verify protected endpoint returns 401 without session."""
    response = client.get("/api/protected")
    
    assert response.status_code == 401
    assert "unauthorized" in response.json()["detail"].lower()


def test_protected_endpoint_with_valid_session(client, authenticated_user):
    """Verify protected endpoint returns 200 with valid session."""
    # First login to get session cookie
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "guard@example.com",
            "password": "GuardPassword123",
        },
    )
    assert login_response.status_code == 200
    
    # Then access protected endpoint
    # TestClient automatically includes cookies from previous requests
    response = client.get("/api/protected")
    
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "guard@example.com"
    assert data["user"]["id"] == authenticated_user.id


def test_protected_endpoint_with_invalid_session(client, authenticated_user):
    """Verify protected endpoint returns 401 with invalid session token."""
    # Try to access with fake session cookie
    client.cookies.set("session", "invalid_token_12345")
    
    response = client.get("/api/protected")
    
    assert response.status_code == 401
    assert "session" in response.json()["detail"].lower()


def test_guard_resolves_correct_user(client, session_with_db):
    """Verify guard resolves the correct authenticated user."""
    # Create two users
    user1 = User(
        email="user1@example.com",
        hashed_password=hash_password("Password123"),
        full_name="User One",
    )
    user2 = User(
        email="user2@example.com",
        hashed_password=hash_password("Password456"),
        full_name="User Two",
    )
    session_with_db.add(user1)
    session_with_db.add(user2)
    session_with_db.commit()
    
    # Login as user1
    login1_response = client.post(
        "/api/auth/login",
        json={
            "email": "user1@example.com",
            "password": "Password123",
        },
    )
    assert login1_response.status_code == 200
    
    # Access protected endpoint
    response = client.get("/api/protected")
    
    # Should resolve user1, not user2
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "user1@example.com"
    assert data["user"]["id"] == user1.id
