
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from pwdlib import PasswordHash
import hashlib
import secrets
from app.core.config import get_settings


settings = get_settings()
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Return a secure password hash for database storage."""
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Compare a submitted password with its stored hash."""
    return password_hasher.verify(password, hashed_password)

def create_password_reset_token() -> str:
    """Generate a cryptographically random reset token."""
    return secrets.token_urlsafe(32)


def hash_password_reset_token(token: str) -> str:
    """Hash a reset token before storing it in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str,
    role: str,
) -> str:
    """Create a signed JWT with an expiration time."""
    now = datetime.now(timezone.utc)

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
