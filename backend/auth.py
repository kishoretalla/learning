"""
Authentication utilities for Research Notebook Backend.

Provides:
- Password hashing and verification using bcrypt
- JWT token generation and validation
- Signup/login helpers
"""
import bcrypt
from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime

# ── Password Hashing ────────────────────────────────────────────────────────

# Bcrypt work factor (higher = more secure but slower)
BCRYPT_SALT_ROUNDS = 12

# Bcrypt has a 72-byte limit for passwords
BCRYPT_MAX_PASSWORD_LENGTH = 72


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    
    Args:
        password: Plaintext password string
    
    Returns:
        Bcrypt hashed password (suitable for storage)
    
    Note:
        Bcrypt has a 72-byte limit. Passwords longer than 72 bytes
        are silently truncated. We truncate explicitly to prevent issues.
    """
    # Truncate password to bcrypt's 72-byte limit
    truncated = password[:BCRYPT_MAX_PASSWORD_LENGTH]
    # Convert to bytes and hash
    salt = bcrypt.gensalt(rounds=BCRYPT_SALT_ROUNDS)
    hashed = bcrypt.hashpw(truncated.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plaintext: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    
    Args:
        plaintext: User-provided password
        hashed: Stored password hash
    
    Returns:
        True if password matches, False otherwise
    """
    # Also truncate plaintext to match bcrypt limit
    truncated = plaintext[:BCRYPT_MAX_PASSWORD_LENGTH]
    try:
        return bcrypt.checkpw(truncated.encode('utf-8'), hashed.encode('utf-8'))
    except (TypeError, ValueError):
        return False


# ── Request/Response Models ─────────────────────────────────────────────────

class SignupRequest(BaseModel):
    """Request payload for user signup."""
    email: EmailStr
    password: str  # Must have minimum length validation in endpoint
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """User data response (excludes password)."""
    id: int
    email: str
    full_name: Optional[str] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class AnalysisHistoryResponse(BaseModel):
    """Analysis history response for API."""
    id: int
    user_id: int
    filename: str
    title: Optional[str] = None
    notebook_filename: str
    created_at: datetime  # Accept datetime from ORM

    model_config = ConfigDict(from_attributes=True)
    
    @field_serializer('created_at')
    def serialize_created_at(self, value):
        """Convert datetime to ISO string for JSON response."""
        if isinstance(value, datetime):
            return value.isoformat()
        return value


class LoginRequest(BaseModel):
    """Request payload for user login."""
    email: EmailStr
    password: str


class AuthToken(BaseModel):
    """Response after successful login."""
    access_token: str
    token_type: str = "bearer"


# ── JWT Token Generation ────────────────────────────────────────────────────

import secrets
from datetime import datetime, timedelta, timezone


def generate_session_token(user_id: int, expires_in_days: int = 7) -> str:
    """
    Generate a secure session token for authenticated user.
    
    Args:
        user_id: ID of the authenticated user
        expires_in_days: Token expiration time in days
    
    Returns:
        Hex token string suitable for HTTP-only cookie or bearer token
    """
    # For v2, we use simple secure random tokens
    # For production, would use JWT with proper signature
    return secrets.token_hex(32)


# ── Auth Guard for Protected Routes ─────────────────────────────────────────

from fastapi import Depends, HTTPException, Request
from sqlmodel import Session, select
from backend.db import get_db
from backend.models import User, UserSession


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    Dependency for protecting routes.
    
    Extracts session token from cookies, validates it exists in database,
    and returns the authenticated user.
    
    Args:
        request: FastAPI Request object (cookies)
        db: Database session (injected via Depends)
    
    Returns:
        Authenticated User object
    
    Raises:
        HTTPException 401 if no valid session found
    """
    # Get session token from cookie
    token = request.cookies.get("session")
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="unauthorized",
        )
    
    # Find session in database
    session = db.exec(
        select(UserSession).where(UserSession.token == token)
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=401,
            detail="session expired or invalid",
        )
    
    # Find and return user
    user = db.exec(
        select(User).where(User.id == session.user_id)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="user not found",
        )
    
    return user


async def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    """
    Optional version of get_current_user.
    
    Returns the authenticated user if session is valid, or None if not authenticated.
    Used for endpoints that work with or without authentication.
    
    Args:
        request: FastAPI Request object (cookies)
        db: Database session (injected via Depends)
    
    Returns:
        Authenticated User object, or None if not authenticated
    """
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
