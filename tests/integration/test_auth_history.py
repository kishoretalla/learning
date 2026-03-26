"""Integration tests for Task 10: Auth + History smoke tests.

Tests the complete user flow:
1. Signup with new account
2. Login with credentials
3. Generate analysis (creates AnalysisHistory)
4. Retrieve analysis history
5. Logout
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.models import User, AnalysisHistory
from backend.auth import hash_password


@pytest.fixture
def client(app_with_db):
    """FastAPI test client with database."""
    return TestClient(app_with_db)


def test_complete_user_flow_signup_login_analyze_history(client, session_with_db):
    """
    Happy path test: Signup → Login → Analyze → View History
    
    Verifies complete v2 sprint workflow.
    """
    # Step 1: Signup
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "email": "complete-flow@example.com",
            "password": "CompleteFlow123",
            "full_name": "Complete Flow User",
        },
    )
    assert signup_response.status_code == 201
    user_data = signup_response.json()
    assert user_data["email"] == "complete-flow@example.com"
    user_id = user_data["id"]
    
    # Step 2: Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "complete-flow@example.com",
            "password": "CompleteFlow123",
        },
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert token_data["token_type"] == "bearer"
    assert "access_token" in token_data
    
    # Verify session cookie was set
    assert client.cookies.get("session") is not None
    
    # Step 3: Generate notebook (creates AnalysisHistory)
    analyze_response = client.post(
        "/api/generate-notebook",
        json={
            "abstract": "Novel approach to machine learning inference",
            "methodologies": ["Transformer Networks", "Attention Mechanisms"],
            "algorithms": ["BERT", "GPT-2"],
            "datasets": ["Wikipedia", "Common Crawl"],
            "results": "Achieved 96% accuracy on GLUE benchmark",
            "conclusions": "Transformers excel at NLP tasks",
            "filename": "ml-research.pdf",
        },
    )
    assert analyze_response.status_code == 200
    assert analyze_response.headers.get("content-disposition")
    
    # Step 4: Retrieve history
    history_response = client.get("/api/history")
    assert history_response.status_code == 200
    histories = history_response.json()
    
    assert len(histories) == 1
    assert histories[0]["user_id"] == user_id
    assert histories[0]["filename"] == "ml-research.pdf"
    assert histories[0]["title"] is not None
    
    # Step 5: Get single analysis
    analysis_id = histories[0]["id"]
    detail_response = client.get(f"/api/history/{analysis_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    
    assert detail["id"] == analysis_id
    assert detail["user_id"] == user_id
    assert detail["filename"] == "ml-research.pdf"
    
    # Step 6: Logout
    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "logged out"
    
    # Verify session cookie is cleared
    assert client.cookies.get("session") is None
    
    # Verify can't access protected endpoints after logout
    protected_response = client.get("/api/history")
    assert protected_response.status_code == 401


def test_auth_flow_with_invalid_credentials(client):
    """Verify proper error handling for invalid credentials."""
    # Signup fails with weak password
    weak_password_response = client.post(
        "/api/auth/signup",
        json={
            "email": "weak@example.com",
            "password": "weak",  # Less than 8 chars
            "full_name": "Weak Password User",
        },
    )
    assert weak_password_response.status_code == 422
    
    # Login fails with wrong password
    # First, create a valid user
    client.post(
        "/api/auth/signup",
        json={
            "email": "valid@example.com",
            "password": "ValidPassword123",
        },
    )
    
    # Try login with wrong password
    wrong_password_response = client.post(
        "/api/auth/login",
        json={
            "email": "valid@example.com",
            "password": "WrongPassword",
        },
    )
    assert wrong_password_response.status_code == 401
    
    # Try login with non-existent email
    nonexistent_response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123",
        },
    )
    assert nonexistent_response.status_code == 401


def test_history_isolation_between_users(client, session_with_db):
    """Verify users can only see their own analysis history."""
    # Create user 1
    client.post(
        "/api/auth/signup",
        json={
            "email": "user1@example.com",
            "password": "User1Password123",
        },
    )
    
    client.post(
        "/api/auth/login",
        json={
            "email": "user1@example.com",
            "password": "User1Password123",
        },
    )
    
    # User 1 generates analysis
    client.post(
        "/api/generate-notebook",
        json={
            "abstract": "User 1's research",
            "methodologies": ["Method 1"],
            "algorithms": ["Algo 1"],
            "datasets": ["Data 1"],
            "results": "Results 1",
            "conclusions": "Conclusions 1",
            "filename": "user1-paper.pdf",
        },
    )
    
    # Get user 1's history
    history1 = client.get("/api/history").json()
    assert len(history1) == 1
    
    # Logout user 1
    client.post("/api/auth/logout")
    
    # Create user 2
    client.post(
        "/api/auth/signup",
        json={
            "email": "user2@example.com",
            "password": "User2Password123",
        },
    )
    
    client.post(
        "/api/auth/login",
        json={
            "email": "user2@example.com",
            "password": "User2Password123",
        },
    )
    
    # User 2 generates analysis
    client.post(
        "/api/generate-notebook",
        json={
            "abstract": "User 2's research",
            "methodologies": ["Method 2"],
            "algorithms": ["Algo 2"],
            "datasets": ["Data 2"],
            "results": "Results 2",
            "conclusions": "Conclusions 2",
            "filename": "user2-paper.pdf",
        },
    )
    
    # Get user 2's history - should only see their own
    history2 = client.get("/api/history").json()
    assert len(history2) == 1
    assert history2[0]["filename"] == "user2-paper.pdf"
    
    # User 2 cannot access user 1's analysis
    user1_analysis_id = history1[0]["id"]
    forbidden_response = client.get(f"/api/history/{user1_analysis_id}")
    assert forbidden_response.status_code == 403


def test_authenticated_endpoints_require_session(client):
    """Verify protected endpoints return 401 without session."""
    # Try to access history without authentication
    history_response = client.get("/api/history")
    assert history_response.status_code == 401
    
    # Try to access protected endpoint
    protected_response = client.get("/api/protected")
    assert protected_response.status_code == 401
    
    # Try to logout without session
    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 401


def test_session_persistence_across_requests(client):
    """Verify session cookie persists across multiple requests."""
    # Signup and login
    client.post(
        "/api/auth/signup",
        json={
            "email": "persistence@example.com",
            "password": "PersistenceTest123",
        },
    )
    
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "persistence@example.com",
            "password": "PersistenceTest123",
        },
    )
    assert login_response.status_code == 200
    
    # Session cookie should persist in TestClient
    session_cookie = client.cookies.get("session")
    assert session_cookie is not None
    
    # Make multiple requests - session should remain valid
    for i in range(3):
        protected_response = client.get("/api/protected")
        assert protected_response.status_code == 200
        
        # Session cookie should remain the same
        assert client.cookies.get("session") == session_cookie
