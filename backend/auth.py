"""
Authentication utilities for Research Notebook Backend.

Provides:
- Password hashing and verification using bcrypt
- JWT token generation and validation
- Signup/login helpers
"""
import bcrypt
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

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
