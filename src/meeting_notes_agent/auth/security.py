"""Authentication security utilities."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import bcrypt
from jose import jwt, JWTError

from meeting_notes_agent.config.core.config import settings


BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    # bcrypt expects bytes, returns bytes
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# JWT token creation
def create_access_token(
    subject: str,
    user_id: int,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {
        "sub": subject,
        "user_id": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4()),
    }
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.algorithm)


def create_refresh_token(
    subject: str,
    user_id: int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT refresh token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    to_encode = {
        "sub": subject,
        "user_id": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4()),
    }
    return jwt.encode(to_encode, settings.jwt_refresh_secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "access":
            raise JWTError("Invalid token type")
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid access token: {str(e)}")


def decode_refresh_token(token: str) -> dict:
    """Decode and validate a refresh token."""
    try:
        payload = jwt.decode(token, settings.jwt_refresh_secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            raise JWTError("Invalid token type")
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid refresh token: {str(e)}")


def create_token_pair(user_id: int, email: str, role: str) -> tuple[str, str]:
    """Create access and refresh token pair."""
    access_token = create_access_token(subject=email, user_id=user_id, role=role)
    refresh_token = create_refresh_token(subject=email, user_id=user_id)
    return access_token, refresh_token


def get_token_expiry(access_token: str) -> Optional[datetime]:
    """Get token expiry from access token."""
    try:
        payload = jwt.decode(access_token, settings.jwt_secret_key, algorithms=[settings.algorithm], options={"verify_exp": False})
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
    except JWTError:
        pass
    return None