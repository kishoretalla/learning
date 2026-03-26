"""
SQLModel definitions for users, sessions, and analysis history.

Provides ORM models for:
- User: Account information with password hash
- UserSession: Authentication tokens and session tracking
- AnalysisHistory: Records of completed paper analyses per user
"""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship


class User(SQLModel, table=True):
    """
    User account model.
    
    Fields:
        id: Auto-generated primary key
        email: Unique email address (login identifier)
        hashed_password: bcrypt-hashed password (never store plaintext)
        full_name: Optional user display name
        created_at: Account creation timestamp (UTC)
        analyses: Relationship to AnalysisHistory records
        sessions: Relationship to UserSession tokens
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, min_length=1, max_length=255)
    hashed_password: str = Field(min_length=1)
    full_name: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    analyses: list["AnalysisHistory"] = Relationship(back_populates="user")
    sessions: list["UserSession"] = Relationship(back_populates="user")


class UserSession(SQLModel, table=True):
    """
    Authentication session token model.
    
    Stores JWT or session tokens tied to users for cookie-based auth.
    
    Fields:
        id: Auto-generated primary key
        user_id: Foreign key to User
        token: Signed JWT or session token
        created_at: Token creation timestamp
        user: Relationship back to User
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    token: str = Field(min_length=1)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    
    # Relationship
    user: User = Relationship(back_populates="sessions")


class AnalysisHistory(SQLModel, table=True):
    """
    Record of a completed paper analysis for a user.
    
    When a user successfully analyzes a paper, an AnalysisHistory record
    is created with metadata about the input and output artifacts.
    
    Fields:
        id: Auto-generated primary key
        user_id: Foreign key to User (owner of this analysis)
        filename: Original PDF filename
        title: User-provided or extracted title of the paper
        notebook_filename: Filename of generated .ipynb artifact
        created_at: Analysis completion timestamp
        user: Relationship back to User
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    filename: str = Field(min_length=1, max_length=1024)
    title: str = Field(max_length=1024)
    notebook_filename: Optional[str] = Field(default=None, max_length=1024)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    
    # Relationship
    user: User = Relationship(back_populates="analyses")
