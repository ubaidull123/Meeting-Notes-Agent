"""Authentication dependencies for FastAPI."""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from meeting_notes_agent.auth.security import decode_access_token, decode_refresh_token
from meeting_notes_agent.database import UserRepository, UserRole, get_db
from meeting_notes_agent.config.core.exceptions import AuthenticationError, AuthorizationError, to_http_exception


# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> Optional["User"]:
    """Get current user if token is valid, otherwise return None."""
    if not credentials:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            return None
    except JWTError:
        return None

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        return None

    return user


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> "User":
    """Get current authenticated user."""
    if not credentials:
        raise to_http_exception(AuthenticationError("Not authenticated"))

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            raise to_http_exception(AuthenticationError("Invalid token payload"))
    except JWTError as e:
        raise to_http_exception(AuthenticationError(str(e)))

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise to_http_exception(AuthenticationError("User not found"))
    if not user.is_active:
        raise to_http_exception(AuthenticationError("Account is disabled"))

    return user


async def get_current_active_user(
    current_user: "User" = Depends(get_current_user),
) -> "User":
    """Get current active user (alias for get_current_user)."""
    return current_user


async def get_current_admin(
    current_user: "User" = Depends(get_current_user),
) -> "User":
    """Get current user and verify admin role."""
    if current_user.role != UserRole.ADMIN:
        raise to_http_exception(AuthorizationError("Admin access required"))
    return current_user


def require_role(*allowed_roles: UserRole):
    """Dependency factory for role-based access control."""
    async def role_checker(current_user: "User" = Depends(get_current_user)) -> "User":
        if current_user.role not in allowed_roles:
            raise to_http_exception(AuthorizationError(f"Requires one of: {', '.join(r.value for r in allowed_roles)}"))
        return current_user
    return role_checker


async def get_current_user_from_refresh_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> "User":
    """Get current user from refresh token."""
    if not credentials:
        raise to_http_exception(AuthenticationError("Not authenticated"))

    try:
        payload = decode_refresh_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            raise to_http_exception(AuthenticationError("Invalid token payload"))
    except JWTError as e:
        raise to_http_exception(AuthenticationError(str(e)))

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise to_http_exception(AuthenticationError("User not found"))
    if not user.is_active:
        raise to_http_exception(AuthenticationError("Account is disabled"))

    return user


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> int:
    """Get current user ID from token (without DB lookup)."""
    if not credentials:
        raise to_http_exception(AuthenticationError("Not authenticated"))

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            raise to_http_exception(AuthenticationError("Invalid token payload"))
    except JWTError as e:
        raise to_http_exception(AuthenticationError(str(e)))

    return user_id


def require_admin(
    current_user: "User" = Depends(get_current_user),
) -> "User":
    """Require admin role."""
    if current_user.role != UserRole.ADMIN:
        raise to_http_exception(AuthorizationError("Admin access required"))
    return current_user


# Import User at the end to avoid circular imports
from meeting_notes_agent.database.models import User