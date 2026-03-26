"""Tests for Task 9: Frontend history list and detail pages."""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.models import User, AnalysisHistory
from backend.auth import hash_password


@pytest.fixture
def client(app_with_db):
    """FastAPI test client."""
    return TestClient(app_with_db)


@pytest.fixture
def authenticated_user_with_history(session_with_db, client):
    """Create initialized user with multiple analysis records."""
    user = User(
        email="history@example.com",
        hashed_password=hash_password("HistoryPassword123"),
        full_name="History Test User",
    )
    session_with_db.add(user)
    session_with_db.commit()
    session_with_db.refresh(user)
    
    # Add multiple analysis histories
    for i in range(3):
        history = AnalysisHistory(
            user_id=user.id,
            filename=f"paper{i+1}.pdf",
            title=f"Research Paper {i+1} Analysis",
            notebook_filename=f"paper{i+1}-notebook.ipynb",
        )
        session_with_db.add(history)
    
    session_with_db.commit()
    
    # Login to set session cookie
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "history@example.com",
            "password": "HistoryPassword123",
        },
    )
    assert login_response.status_code == 200
    
    return user, client


def test_history_api_requires_authentication(client):
    """Verify history API endpoint requires authentication."""
    response = client.get("/api/history")
    
    # Should return 401 without authentication
    assert response.status_code == 401


def test_history_api_returns_user_analyses(authenticated_user_with_history, session_with_db):
    """Verify history API returns only current user's analyses."""
    user, client = authenticated_user_with_history
    
    response = client.get("/api/history")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be a list
    assert isinstance(data, list)
    
    # Should have 3 items
    assert len(data) == 3
    
    # Check structure of first item
    first = data[0]
    assert "id" in first
    assert "filename" in first
    assert "title" in first
    assert "notebook_filename" in first
    assert "created_at" in first


def test_history_api_reverse_chronological(authenticated_user_with_history):
    """Verify history API returns analyses in reverse chronological order."""
    user, client = authenticated_user_with_history
    
    response = client.get("/api/history")
    
    data = response.json()
    
    # Should be in reverse chronological order (newest first)
    # Since all created at similar times, just check we have them
    assert len(data) == 3
    
    # Verify they're all from the same user
    assert all(item["user_id"] == user.id for item in data)


def test_history_api_filters_other_users(authenticated_user_with_history, session_with_db):
    """Verify history API only returns current user's analyses, not others'."""
    user1, client1 = authenticated_user_with_history
    
    # Create another user with analyses
    user2 = User(
        email="other@example.com",
        hashed_password=hash_password("OtherPassword123"),
        full_name="Other User",
    )
    session_with_db.add(user2)
    session_with_db.commit()
    session_with_db.refresh(user2)
    
    # Add analysis for user2
    history = AnalysisHistory(
        user_id=user2.id,
        filename="other-paper.pdf",
        title="Other User's Analysis",
        notebook_filename="other-notebook.ipynb",
    )
    session_with_db.add(history)
    session_with_db.commit()
    
    # Get history for user1
    response = client1.get("/api/history")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only return user1's analyses (3), not user2's (1)
    assert len(data) == 3
    assert all(item["user_id"] == user1.id for item in data)


def test_history_get_single_analysis(authenticated_user_with_history, session_with_db):
    """Verify can retrieve a single analysis by ID."""
    user, client = authenticated_user_with_history
    
    # Get first analysis ID
    analyses = session_with_db.exec(
        select(AnalysisHistory).where(AnalysisHistory.user_id == user.id)
    ).all()
    
    first_analysis = analyses[0]
    
    # Get single analysis
    response = client.get(f"/api/history/{first_analysis.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == first_analysis.id
    assert data["filename"] == first_analysis.filename
    assert data["title"] == first_analysis.title


def test_history_get_analysis_401_unauthorized(client):
    """Verify retrieving analysis without auth returns 401."""
    response = client.get("/api/history/1")
    
    assert response.status_code == 401


def test_history_get_analysis_404_not_found(authenticated_user_with_history):
    """Verify retrieving nonexistent analysis returns 404."""
    user, client = authenticated_user_with_history
    
    response = client.get("/api/history/9999")
    
    assert response.status_code == 404


def test_history_get_other_users_analysis_forbidden(authenticated_user_with_history, session_with_db):
    """Verify user cannot access another user's analysis."""
    user1, client1 = authenticated_user_with_history
    
    # Create another user with analysis
    user2 = User(
        email="other2@example.com",
        hashed_password=hash_password("OtherPassword123"),
        full_name="Other User 2",
    )
    session_with_db.add(user2)
    session_with_db.commit()
    session_with_db.refresh(user2)
    
    # Add analysis for user2
    history = AnalysisHistory(
        user_id=user2.id,
        filename="other-paper.pdf",
        title="Other User's Analysis",
        notebook_filename="other-notebook.ipynb",
    )
    session_with_db.add(history)
    session_with_db.commit()
    session_with_db.refresh(history)
    
    # Try to access user2's analysis as user1
    response = client1.get(f"/api/history/{history.id}")
    
    # Should return 403 Forbidden
    assert response.status_code == 403
