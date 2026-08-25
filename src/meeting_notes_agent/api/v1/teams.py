"""Team workspace and membership routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from meeting_notes_agent.auth.dependencies import enforce_active_team_resource_scope, get_current_user
from meeting_notes_agent.database import get_db
from meeting_notes_agent.database.models import User
from meeting_notes_agent.schemas.team import (
    TeamCreate,
    TeamListItem,
    TeamMemberAdd,
    TeamMemberResponse,
    TeamMemberRoleUpdate,
    TeamResponse,
    TeamUpdate,
)
from meeting_notes_agent.services.team_service import TeamService


router = APIRouter(prefix="/teams", tags=["Teams"], dependencies=[Depends(enforce_active_team_resource_scope)])


@router.post("", response_model=TeamListItem, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return TeamService(db).create_team(current_user.id, data)


@router.get("", response_model=list[TeamListItem])
async def list_teams(
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return TeamService(db).list_teams(current_user.id)


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return TeamService(db).get_team(team_id, current_user.id)


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    data: TeamUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return TeamService(db).update_team(team_id, current_user.id, data)


@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_team_members(
    team_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return TeamService(db).list_members(team_id, current_user.id)


@router.post(
    "/{team_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_team_member(
    team_id: UUID,
    data: TeamMemberAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return TeamService(db).add_member(team_id, current_user.id, data)


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_team_member_role(
    team_id: UUID,
    user_id: int,
    data: TeamMemberRoleUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    return TeamService(db).update_member_role(
        team_id, user_id, current_user.id, data.role
    )


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: UUID,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    TeamService(db).remove_member(team_id, user_id, current_user.id)


@router.delete(
    "/{team_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_team_invitation(
    team_id: UUID,
    invitation_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db=Depends(get_db),
):
    TeamService(db).revoke_invitation(team_id, invitation_id, current_user.id)
