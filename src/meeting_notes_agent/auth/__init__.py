"""Authentication module for Meeting Notes API."""
from meeting_notes_agent.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    create_token_pair,
    get_token_expiry,
)
from meeting_notes_agent.auth.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_current_active_user,
    get_current_admin,
    get_current_user_from_refresh_token,
    require_role,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "decode_refresh_token",
    "create_token_pair",
    "get_token_expiry",
    "get_current_user",
    "get_current_user_optional",
    "get_current_active_user",
    "get_current_admin",
    "get_current_user_from_refresh_token",
    "require_role",
]