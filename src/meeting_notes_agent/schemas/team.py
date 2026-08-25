"""Team and team-membership API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from meeting_notes_agent.database.models import TeamRole


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class TeamListItem(BaseModel):
    id: UUID
    name: str
    description: str | None
    role: TeamRole
    created_by: int
    created_at: datetime
    updated_at: datetime


class TeamResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamMemberAdd(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    title: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=255)
    role: TeamRole = TeamRole.MEMBER
    user_id: int | None = Field(default=None, gt=0, exclude=True)

    @model_validator(mode="after")
    def require_person_identity(self) -> "TeamMemberAdd":
        if self.user_id is None and (not self.full_name or self.email is None):
            raise ValueError("Name and email are required")
        return self


class TeamMemberRoleUpdate(BaseModel):
    role: TeamRole


class TeamMemberResponse(BaseModel):
    id: UUID
    team_id: UUID
    user_id: int | None
    role: TeamRole
    email: str
    full_name: str
    title: str | None = None
    department: str | None = None
    status: str = "active"
    is_active: bool
    accepted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
