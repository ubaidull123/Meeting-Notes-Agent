"""Team-scoped project and membership routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from meeting_notes_agent.auth.dependencies import enforce_active_team_resource_scope, get_current_user
from meeting_notes_agent.database import get_db
from meeting_notes_agent.database.models import User
from meeting_notes_agent.schemas.project import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)
from meeting_notes_agent.services.project_service import ProjectService


router = APIRouter(tags=["Projects"], dependencies=[Depends(enforce_active_team_resource_scope)])


@router.post(
    "/teams/{team_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    team_id: UUID,
    data: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return ProjectService(db).create_project(team_id, current_user.id, data)


@router.get("/teams/{team_id}/projects", response_model=list[ProjectResponse])
async def list_projects(
    team_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return ProjectService(db).list_projects(team_id, current_user.id)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return ProjectService(db).get_project(project_id, current_user.id)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return ProjectService(db).update_project(project_id, current_user.id, data)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    ProjectService(db).delete_project(project_id, current_user.id)


@router.get(
    "/projects/{project_id}/members", response_model=list[ProjectMemberResponse]
)
async def list_project_members(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return ProjectService(db).list_members(project_id, current_user.id)


@router.post(
    "/projects/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: UUID,
    data: ProjectMemberAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return ProjectService(db).add_member(project_id, data.user_id, current_user.id)


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_project_member(
    project_id: UUID,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    ProjectService(db).remove_member(project_id, user_id, current_user.id)
