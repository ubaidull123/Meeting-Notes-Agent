"""Admin API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional, List
from uuid import UUID
from datetime import datetime

from meeting_notes_agent.auth.dependencies import get_current_user, require_admin
from meeting_notes_agent.database.models import User, MeetingStatus
from meeting_notes_agent.schemas.admin import (
    AdminStatsResponse,
    AdminUserListItem,
    AdminUserDetail,
    AdminUserUpdate,
    AdminMeetingListItem,
    AdminMeetingStatusResponse,
)
from meeting_notes_agent.schemas.user import UserQuotaResponse, UserCreditsResponse
from meeting_notes_agent.services import AdminService
from meeting_notes_agent.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    _admin: Annotated[User, Depends(require_admin)],
):
    """Get admin dashboard statistics."""
    admin_service = AdminService()
    return admin_service.get_stats()


@router.get("/users", response_model=List[AdminUserListItem])
async def list_users(
    _admin: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List all users (admin)."""
    from meeting_notes_agent.database.models import UserRole
    role_enum = UserRole(role) if role else None

    admin_service = AdminService()
    users, total = admin_service.list_users(
        page=page,
        page_size=page_size,
        search=search,
        role=role_enum,
        is_active=is_active,
    )
    return users


@router.get("/users/{user_id}", response_model=AdminUserDetail)
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


@router.patch("/users/{user_id}", response_model=AdminUserDetail)
async def update_user(
    user_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    data: AdminUserUpdate,
):
    """Update user (admin)."""
    admin_service = AdminService()
    try:
        return admin_service.update_user(user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.post("/users/{user_id}/credits", response_model=UserCreditsResponse)
async def adjust_user_credits(
    user_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    amount: int,
    reason: str,
):
    """Adjust user credits (admin)."""
    admin_service = AdminService()
    try:
        return admin_service.adjust_credits(user_id, amount, reason)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users/{user_id}/quota", response_model=UserQuotaResponse)
async def adjust_user_quota(
    user_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    monthly_limit: int,
):
    """Adjust user quota (admin)."""
    admin_service = AdminService()
    try:
        return admin_service.adjust_quota(user_id, monthly_limit)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/meetings", response_model=List[AdminMeetingListItem])
async def list_meetings(
    _admin: Annotated[User, Depends(require_admin)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    """List all meetings (admin)."""
    status_enum = MeetingStatus(status) if status else None

    admin_service = AdminService()
    meetings, total = admin_service.list_meetings(
        page=page,
        page_size=page_size,
        status=status_enum,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )
    return meetings


@router.get("/meetings/{meeting_id}", response_model=AdminMeetingStatusResponse)
async def get_meeting_status(
    meeting_id: UUID,
    _admin: Annotated[User, Depends(require_admin)],
):
    """Get meeting status (admin)."""
    admin_service = AdminService()
    try:
        return admin_service.get_meeting_status(meeting_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/meetings/{meeting_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_meeting(
    meeting_id: UUID,
    _admin: Annotated[User, Depends(require_admin)],
):
    """Cancel meeting (admin)."""
    admin_service = AdminService()
    try:
        admin_service.cancel_meeting(meeting_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/meetings/{meeting_id}/retry", status_code=status.HTTP_204_NO_CONTENT)
async def retry_meeting(
    meeting_id: UUID,
    _admin: Annotated[User, Depends(require_admin)],
):
    """Retry failed meeting (admin)."""
    admin_service = AdminService()
    try:
        admin_service.retry_meeting(meeting_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
