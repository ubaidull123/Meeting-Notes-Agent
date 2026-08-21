"""Users API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional
from pydantic import BaseModel

from meeting_notes_agent.auth.dependencies import get_current_user_id, get_current_user, require_admin
from meeting_notes_agent.database.models import User, UserRole
from meeting_notes_agent.schemas.user import (
    UserProfileResponse,
    UserQuotaResponse,
    UserCreditsResponse,
    UserUsageResponse,
)
from meeting_notes_agent.schemas.auth import ChangePasswordRequest
from meeting_notes_agent.schemas.admin import AdminUserListItem, AdminUserDetail, AdminUserUpdate
from meeting_notes_agent.services import AuthService, AdminService
from meeting_notes_agent.core.exceptions import NotFoundError, ValidationError, AuthenticationError

router = APIRouter(prefix="/users", tags=["Users"])


class UpdateProfileRequest(BaseModel):
    """Update profile request."""
    full_name: str


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(current_user_id: Annotated[int, Depends(get_current_user_id)]):
    """Get current user profile with quota, credits, and usage."""
    auth_service = AuthService()
    try:
        return auth_service.get_profile(current_user_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    data: UpdateProfileRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Update current user profile."""
    auth_service = AuthService()
    try:
        return auth_service.update_profile(current_user_id, data.full_name)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    data: ChangePasswordRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Change current user password."""
    from meeting_notes_agent.schemas.auth import ChangePasswordRequest
    auth_service = AuthService()
    try:
        auth_service.change_password(current_user_id, data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


# Admin routes
@router.get("", response_model=list[AdminUserListItem])
async def list_users(
    _admin: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
):
    """List all users (admin)."""
    admin_service = AdminService()
    users, total = admin_service.list_users(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        is_active=is_active,
    )
    return users


@router.get("/{user_id}", response_model=AdminUserDetail)
async def get_user(
    user_id: int,
    _admin: Annotated[User, Depends(require_admin)],
):
    """Get user detail (admin)."""
    admin_service = AdminService()
    try:
        return admin_service.get_user(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{user_id}", response_model=AdminUserDetail)
async def update_user(
    user_id: int,
    data: AdminUserUpdate,
    _admin: Annotated[User, Depends(require_admin)],
):
    """Update user (admin)."""
    admin_service = AdminService()
    try:
        return admin_service.update_user(user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin: Annotated[User, Depends(require_admin)],
):
    """Delete user (admin)."""
    admin_service = AdminService()
    try:
        admin_service.delete_user(user_id, current_admin_id=admin.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{user_id}/credits", response_model=UserCreditsResponse)
async def adjust_user_credits(
    user_id: int,
    amount: int,
    reason: str,
    _admin: Annotated[User, Depends(require_admin)],
):
    """Adjust user credits (admin)."""
    admin_service = AdminService()
    try:
        return admin_service.adjust_credits(user_id, amount, reason)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{user_id}/quota", response_model=UserQuotaResponse)
async def adjust_user_quota(
    user_id: int,
    monthly_limit: int,
    _admin: Annotated[User, Depends(require_admin)],
):
    """Adjust user quota (admin)."""
    admin_service = AdminService()
    try:
        return admin_service.adjust_quota(user_id, monthly_limit)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
