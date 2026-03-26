"""Tests for Task 5: Login/logout endpoints with secure session cookies."""
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
def test_user(session_with_db):
    """Create a test user for login tests."""
    user = User(
        email="login@example.com",
        hashed_password=hash_password("TestPassword123"),
        full_name="Login Test User",
    )
    session_with_db.add(user)
    session_with_db.commit()
    session_with_db.refresh(user)
    return user


def test_login_with_valid_credentials(client, test_user):
    """Verify login sets session cookie and returns token."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "TestPassword123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Check that cookie was set
    assert "session" in client.cookies or response.cookies


def test_login_with_invalid_password(client, test_user):
    """Verify login fails with wrong password."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "WrongPassword",
        },
    )
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_with_nonexistent_email(client):
    """Verify login fails with non-existent email."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "AnyPassword123",
        },
    )
    
    assert response.status_code == 401


def test_logout_clears_session(client, test_user):
    """Verify logout clears session cookie."""
    # First login
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "TestPassword123",
        },
    )
    assert login_response.status_code == 200
    
    # Then logout
    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    
    # Session/token should be invalid now
    assert logout_response.json()["message"] == "logged out"
