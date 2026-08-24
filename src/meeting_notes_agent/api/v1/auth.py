"""Auth API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from meeting_notes_agent.auth.dependencies import get_current_user_id, get_current_user
from meeting_notes_agent.database.models import User
from meeting_notes_agent.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from meeting_notes_agent.schemas.user import UserProfileResponse
from meeting_notes_agent.services import AuthService
from meeting_notes_agent.config.core.exceptions import AuthenticationError, ValidationError, ConflictError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister):
    """Register a new user."""
    auth_service = AuthService()
    try:
        user = auth_service.register(data)
        return user
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    """Login and get access/refresh tokens."""
    auth_service = AuthService()
    try:
        access_token, refresh_token = auth_service.login(data)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,  # 15 minutes
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(data: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    auth_service = AuthService()
    try:
        access_token, refresh_token = auth_service.refresh_tokens(data.refresh_token)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=900,
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user_id: Annotated[int, Depends(get_current_user_id)]):
    """Logout (client should discard tokens)."""
    # In a stateless JWT setup, logout is client-side
    # Could implement token blacklist here if needed
    pass


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user_id: Annotated[int, Depends(get_current_user_id)]):
    """Get current user profile."""
    auth_service = AuthService()
    try:
        return auth_service.get_profile(current_user_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    full_name: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Update current user profile."""
    auth_service = AuthService()
    try:
        return auth_service.update_profile(current_user_id, full_name)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Change current user password."""
    auth_service = AuthService()
    try:
        auth_service.change_password(current_user_id, data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(data: ForgotPasswordRequest):
    """Request password reset (placeholder - implement email sending)."""
    # TODO: Implement password reset email
    pass


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(data: ResetPasswordRequest):
    """Reset password with token (placeholder)."""
    # TODO: Implement password reset with token
    pass


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(data: VerifyEmailRequest):
    """Verify email with token (placeholder)."""
    # TODO: Implement email verification
    pass