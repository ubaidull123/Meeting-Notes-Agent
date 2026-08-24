"""User schemas."""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from meeting_notes_agent.database.models import PlatformRole, UserRole


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str
    role: UserRole
    platform_role: PlatformRole = PlatformRole.USER
    is_active: bool


class UserCreate(UserBase):
    """User creation schema (admin)."""
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """User update schema."""
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserUpdateSelf(BaseModel):
    """User self-update schema (limited fields)."""
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)


class UserResponse(UserBase):
    """User response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "USER",
                "platform_role": "user",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }
    )


class UserAdminResponse(UserResponse):
    """Admin user response with additional fields."""
    quota: Optional["UserQuotaResponse"] = None
    credits: Optional["UserCreditsResponse"] = None
    usage: Optional[List["UserUsageResponse"]] = None


class UserProfileResponse(BaseModel):
    """Current user profile response."""
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    platform_role: PlatformRole
    is_active: bool
    created_at: datetime
    quota: Optional["UserQuotaResponse"] = None
    credits: Optional["UserCreditsResponse"] = None
    usage: Optional[List["UserUsageResponse"]] = None

    model_config = ConfigDict(from_attributes=True)


class UserQuotaResponse(BaseModel):
    """User quota response."""
    user_id: int
    monthly_meeting_limit: int
    monthly_credits: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserQuotaUpdate(BaseModel):
    """User quota update schema (admin)."""
    monthly_meeting_limit: Optional[int] = Field(default=None, ge=1, le=1000)
    monthly_credits: Optional[int] = Field(default=None, ge=0, le=10000)


class UserCreditsResponse(BaseModel):
    """User credits response."""
    user_id: int
    balance: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreditsAdjust(BaseModel):
    """User credits adjustment schema (admin)."""
    amount: int = Field(..., description="Positive to add, negative to remove")
    reason: str = Field(..., min_length=1, max_length=500)


class UserUsageResponse(BaseModel):
    """User usage response."""
    id: str
    user_id: int
    month: str  # YYYY-MM-DD
    meetings_processed: int
    tokens_used: int
    credits_consumed: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    @field_validator("month", mode="before")
    @classmethod
    def serialize_month(cls, value):
        if isinstance(value, date):
            return value.isoformat()
        return value


# Forward references
UserAdminResponse.model_rebuild()
UserProfileResponse.model_rebuild()
