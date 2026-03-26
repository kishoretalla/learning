"""
Integration tests for Task 4: Signup endpoint with password hashing.

Verifies:
1. Signup endpoint creates users with hashed passwords
2. Duplicate email signup is rejected
3. Password is never stored plaintext
4. Endpoint returns appropriate HTTP status codes
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.models import User


@pytest.fixture
def client(app_with_db):
    """FastAPI test client with database dependency override."""
    return TestClient(app_with_db)


def test_signup_creates_user(client, session_with_db):
    """Verify POST /api/auth/signup creates a user with hashed password."""
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data
    # Password should NOT be in response
    assert "password" not in data
    assert "hashed_password" not in data


def test_signup_duplicate_email_rejected(client, session_with_db):
    """Verify signup rejects duplicate email."""
    # First signup
    response1 = client.post(
        "/api/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "Password123!",
        },
    )
    assert response1.status_code == 201
    
    # Second signup with same email
    response2 = client.post(
        "/api/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "DifferentPassword456!",
        },
    )
    assert response2.status_code == 409  # Conflict
    assert "already exists" in response2.json()["detail"].lower()


def test_signup_validates_email_format(client):
    """Verify signup validates email format."""
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "not-an-email",
            "password": "Password123!",
        },
    )
    assert response.status_code == 422  # Validation error


def test_signup_validates_password_length(client):
    """Verify signup requires password (cannot be empty)."""
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "test@example.com",
            "password": "",  # Empty password
        },
    )
    assert response.status_code == 422


def test_signup_password_is_hashed(client, session_with_db):
    """Verify password is hashed, not stored plaintext."""
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "hashedtest@example.com",
            "password": "MyPlaintextPassword123!",
        },
    )
    assert response.status_code == 201
    
    # Verify in database that password is hashed, not plaintext
    user = session_with_db.exec(
        select(User).where(User.email == "hashedtest@example.com")
    ).first()
    
    assert user is not None
    # Bcrypt hashes should start with $2b$
    assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2y$")
    # Plaintext password should NOT be in hashed_password field
    assert "MyPlaintextPassword123!" not in user.hashed_password


def test_signup_returns_user_data(client):
    """Verify signup returns created user data."""
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "response-test@example.com",
            "password": "Password123!",
            "full_name": "Response Test User",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "response-test@example.com"
    assert data["full_name"] == "Response Test User"
    assert "created_at" in data
