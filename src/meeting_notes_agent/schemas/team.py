"""Team and team-membership API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    user_id: int
    role: TeamRole = TeamRole.MEMBER


class TeamMemberRoleUpdate(BaseModel):
    role: TeamRole


class TeamMemberResponse(BaseModel):
    id: UUID
    team_id: UUID
    user_id: int
    role: TeamRole
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
