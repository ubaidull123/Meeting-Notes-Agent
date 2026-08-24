"""Project and project-membership API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    context: str | None = None
    member_ids: list[int] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    context: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    team_id: UUID
    name: str
    description: str | None
    context: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberAdd(BaseModel):
    user_id: int


class ProjectMemberResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
