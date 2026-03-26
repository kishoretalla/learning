"""
Pytest configuration and shared fixtures for integration tests.
"""
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, SQLModel

# Import models to register them with SQLModel.metadata BEFORE creating engine
from backend import models as _models  # noqa: F401


@pytest.fixture
def session_with_db():
    """
    Create a test database with SQLModel tables and return a session.
    Uses in-memory SQLite for fast tests.
    """
    # Create in-memory SQLite engine for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables from SQLModel models
    # Models must be imported before this call
    SQLModel.metadata.create_all(engine)
    
    # Yield a session
    with Session(engine) as session:
        yield session
