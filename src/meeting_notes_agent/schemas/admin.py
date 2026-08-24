"""Admin schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from meeting_notes_agent.database.models import UserRole, MeetingStatus


class AdminStatsResponse(BaseModel):
    """Admin dashboard statistics response."""
    total_users: int
    active_users: int
    total_meetings: int
    meetings_today: int
    meetings_this_week: int
    meetings_this_month: int
    successful_meetings: int
    failed_meetings: int
    processing_meetings: int
    total_tokens_used: int
    emails_sent: int
    total_credits_issued: int
    total_credits_consumed: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_users": 150,
                "active_users": 120,
                "total_meetings": 1250,
                "meetings_today": 5,
                "meetings_this_week": 42,
                "meetings_this_month": 180,
                "successful_meetings": 1180,
                "failed_meetings": 35,
                "processing_meetings": 3,
                "total_tokens_used": 2500000,
                "emails_sent": 1100,
                "total_credits_issued": 75000,
                "total_credits_consumed": 45000
            }
        }
    )


class AdminUserListItem(BaseModel):
    """Admin user list item."""
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    quota_limit: int
    credits_balance: int
    meetings_this_month: int

    model_config = ConfigDict(from_attributes=True)


class AdminUserDetail(BaseModel):
    """Admin user detail response."""
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    quota: Optional["UserQuotaResponse"] = None
    credits: Optional["UserCreditsResponse"] = None
    usage: Optional[List["UserUsageResponse"]] = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserUpdate(BaseModel):
    """Admin user update schema."""
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class AdminMeetingListItem(BaseModel):
    """Admin meeting list item."""
    id: UUID
    user_id: int
    user_email: str
    user_name: str
    title: str
    meeting_date: datetime
    status: MeetingStatus
    tokens_used: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminMeetingStatusResponse(BaseModel):
    """Admin meeting status response."""
    meeting_id: UUID
    user_id: int
    user_email: str
    title: str
    status: MeetingStatus
    current_stage: Optional[str] = None
    error_code: Optional[str]
    error_message: Optional[str]
    tokens_used: int
    created_at: datetime
    updated_at: datetime
    thread_id: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# Import here to avoid circular imports
from meeting_notes_agent.schemas.user import UserQuotaResponse, UserCreditsResponse, UserUsageResponse