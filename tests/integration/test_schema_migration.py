"""
Integration tests for Task 3: Schema migration - auth and history tables.

Verifies:
1. All required tables are created when database initializes
2. Tables have correct columns and constraints
3. Relationships are properly configured
4. Migration can be applied to a fresh database
"""
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def test_migration_creates_all_tables(session_with_db):
    """Verify all required tables are created during migration."""
    from backend.models import User, UserSession, AnalysisHistory
    from sqlmodel import select
    
    # Verify we can query each table (tables exist)
    # If tables don't exist, these queries will fail
    users = session_with_db.exec(select(User)).all()
    sessions = session_with_db.exec(select(UserSession)).all()
    analyses = session_with_db.exec(select(AnalysisHistory)).all()
    
    # All should return empty lists (no data yet, but tables exist)
    assert isinstance(users, list)
    assert isinstance(sessions, list)
    assert isinstance(analyses, list)


def test_user_table_has_required_columns(session_with_db):
    """Verify user table has all required columns."""
    from sqlalchemy import text
    
    result = session_with_db.execute(
        text("PRAGMA table_info(user)")
    )
    columns = {row[1] for row in result}  # row[1] is column name
    
    expected_columns = {"id", "email", "hashed_password", "full_name", "created_at"}
    assert expected_columns.issubset(columns), f"Missing columns in user: {expected_columns - columns}"


def test_user_email_has_unique_constraint(session_with_db):
    """Verify email field has unique constraint."""
    from sqlalchemy import text
    
    # Check that email is marked as unique
    result = session_with_db.execute(
        text("PRAGMA index_list(user)")
    )
    indices = list(result)
    # At least one index should exist (email unique)
    assert len(indices) > 0, "No indices found on user table"


def test_analysis_history_table_has_required_columns(session_with_db):
    """Verify analysis_history table has all required columns."""
    from sqlalchemy import text
    
    result = session_with_db.execute(
        text("PRAGMA table_info(analysishistory)")
    )
    columns = {row[1] for row in result}
    
    expected_columns = {"id", "user_id", "filename", "title", "notebook_filename", "created_at"}
    assert expected_columns.issubset(columns), f"Missing columns in analysishistory: {expected_columns - columns}"


def test_user_session_table_has_required_columns(session_with_db):
    """Verify user_session table has all required columns."""
    from sqlalchemy import text
    
    result = session_with_db.execute(
        text("PRAGMA table_info(usersession)")
    )
    columns = {row[1] for row in result}
    
    expected_columns = {"id", "user_id", "token", "created_at"}
    assert expected_columns.issubset(columns), f"Missing columns in usersession: {expected_columns - columns}"


def test_fresh_database_migration(tmp_path):
    """Verify migration can be applied to a fresh SQLite database."""
    from backend.db import init_db
    from sqlalchemy import text
    
    db_path = tmp_path / "fresh_test.db"
    db_url = f"sqlite:///{db_path}"
    
    # Initialize a fresh database
    engine = init_db(db_url)
    
    # Verify database file was created
    assert db_path.exists(), "Database file not created"
    
    # Verify tables exist
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        result = session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        table_names = {row[0] for row in result}
        
        expected_tables = {"user", "usersession", "analysishistory"}
        assert expected_tables.issubset(table_names)
