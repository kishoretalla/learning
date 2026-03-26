"""
Integration tests for Task 2: User and analysis history database models.

Verifies:
1. User model can be created and queried
2. AnalysisHistory model can be created with user relationship
3. Timestamps are set correctly
4. Models are compatible with SQLModel + SQLAlchemy
"""
import pytest
from datetime import datetime, timezone
from sqlmodel import Session, select

# Import from backend (will be created in Task 2)
from backend.models import User, AnalysisHistory, UserSession


def test_user_model_creation(session_with_db):
    """Verify User model can be created with required fields."""
    user = User(
        email="test@example.com",
        hashed_password="$2b$12$abc123...",  # Placeholder bcrypt hash
        full_name="Test User",
    )
    session_with_db.add(user)
    session_with_db.commit()
    session_with_db.refresh(user)
    
    # Verify fields
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)


def test_user_email_uniqueness(session_with_db):
    """Verify User.email constraint (should be unique)."""
    user1 = User(email="unique@example.com", hashed_password="hash1")
    user2 = User(email="unique@example.com", hashed_password="hash2")
    
    session_with_db.add(user1)
    session_with_db.commit()
    
    session_with_db.add(user2)
    with pytest.raises(Exception):  # SQLAlchemy IntegrityError
        session_with_db.commit()
    session_with_db.rollback()


def test_analysis_history_model_creation(session_with_db):
    """Verify AnalysisHistory model can be created with user relationship."""
    # Create a user first
    user = User(email="researcher@example.com", hashed_password="hash")
    session_with_db.add(user)
    session_with_db.commit()
    session_with_db.refresh(user)
    
    # Create analysis history
    analysis = AnalysisHistory(
        user_id=user.id,
        filename="research-paper.pdf",
        title="A Great Research Paper",
        notebook_filename="notebook-123.ipynb",
    )
    session_with_db.add(analysis)
    session_with_db.commit()
    session_with_db.refresh(analysis)
    
    # Verify fields
    assert analysis.id is not None
    assert analysis.user_id == user.id
    assert analysis.filename == "research-paper.pdf"
    assert analysis.title == "A Great Research Paper"
    assert analysis.notebook_filename == "notebook-123.ipynb"
    assert analysis.created_at is not None


def test_analysis_history_user_relationship(session_with_db):
    """Verify relationship between AnalysisHistory and User."""
    user = User(email="researcher2@example.com", hashed_password="hash")
    session_with_db.add(user)
    session_with_db.commit()
    session_with_db.refresh(user)
    
    # Create multiple analyses for same user
    analysis1 = AnalysisHistory(user_id=user.id, filename="paper1.pdf", title="Paper 1")
    analysis2 = AnalysisHistory(user_id=user.id, filename="paper2.pdf", title="Paper 2")
    
    session_with_db.add(analysis1)
    session_with_db.add(analysis2)
    session_with_db.commit()
    
    # Query user and verify relationship
    retrieved_user = session_with_db.exec(
        select(User).where(User.id == user.id)
    ).first()
    
    assert retrieved_user is not None
    assert len(retrieved_user.analyses) == 2
    assert retrieved_user.analyses[0].filename == "paper1.pdf"


def test_user_session_model(session_with_db):
    """Verify UserSession model for storing authentication tokens."""
    user = User(email="session-user@example.com", hashed_password="hash")
    session_with_db.add(user)
    session_with_db.commit()
    session_with_db.refresh(user)
    
    token = "eyJhbGciOiJIUzI1NiIs..."
    user_session = UserSession(
        user_id=user.id,
        token=token,
    )
    session_with_db.add(user_session)
    session_with_db.commit()
    session_with_db.refresh(user_session)
    
    assert user_session.id is not None
    assert user_session.user_id == user.id
    assert user_session.token == token
    assert user_session.created_at is not None
