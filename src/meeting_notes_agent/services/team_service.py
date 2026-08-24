"""Transactional team and team-membership operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError

from meeting_notes_agent.config.core.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from meeting_notes_agent.database import get_db
from meeting_notes_agent.database.models import (
    Project,
    ProjectMembership,
    Team,
    TeamMembership,
    TeamRole,
    User,
)
from meeting_notes_agent.schemas.team import (
    TeamCreate,
    TeamListItem,
    TeamMemberAdd,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdate,
)
from meeting_notes_agent.services.authorization_service import AuthorizationService


class TeamService:
    def __init__(self, db=None):
        self.db = db

    def _get_db(self):
        return self.db or next(get_db())

    @staticmethod
    def _member_response(membership: TeamMembership) -> TeamMemberResponse:
        return TeamMemberResponse(
            id=membership.id,
            team_id=membership.team_id,
            user_id=membership.user_id,
            role=membership.role,
            email=membership.user.email,
            full_name=membership.user.full_name,
            is_active=membership.user.is_active,
            created_at=membership.created_at,
            updated_at=membership.updated_at,
        )

    def create_team(self, user_id: int, data: TeamCreate) -> TeamResponse:
        db = self._get_db()
        user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
        if user is None:
            raise NotFoundError("User not found")
        team = Team(
            name=data.name.strip(),
            description=data.description,
            created_by=user_id,
        )
        db.add(team)
        db.flush()
        db.add(TeamMembership(team_id=team.id, user_id=user_id, role=TeamRole.OWNER))
        db.commit()
        db.refresh(team)
        return TeamResponse.model_validate(team)

    def list_teams(self, user_id: int) -> list[TeamListItem]:
        db = self._get_db()
        memberships = (
            db.query(TeamMembership)
            .join(Team)
            .filter(TeamMembership.user_id == user_id)
            .order_by(Team.name.asc())
            .all()
        )
        return [
            TeamListItem(
                id=membership.team.id,
                name=membership.team.name,
                description=membership.team.description,
                role=membership.role,
                created_by=membership.team.created_by,
                created_at=membership.team.created_at,
                updated_at=membership.team.updated_at,
            )
            for membership in memberships
        ]

    def get_team(self, team_id: UUID, user_id: int) -> TeamResponse:
        db = self._get_db()
        AuthorizationService(db).require_team_member(team_id, user_id)
        team = db.query(Team).filter(Team.id == team_id).one()
        return TeamResponse.model_validate(team)

    def update_team(self, team_id: UUID, user_id: int, data: TeamUpdate) -> TeamResponse:
        db = self._get_db()
        AuthorizationService(db).require_team_admin(team_id, user_id)
        team = db.query(Team).filter(Team.id == team_id).one()
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes:
            changes["name"] = changes["name"].strip()
        for field, value in changes.items():
            setattr(team, field, value)
        db.commit()
        db.refresh(team)
        return TeamResponse.model_validate(team)

    def list_members(self, team_id: UUID, user_id: int) -> list[TeamMemberResponse]:
        db = self._get_db()
        AuthorizationService(db).require_team_admin(team_id, user_id)
        memberships = (
            db.query(TeamMembership)
            .join(User)
            .filter(TeamMembership.team_id == team_id)
            .order_by(User.full_name.asc())
            .all()
        )
        return [self._member_response(item) for item in memberships]

    def add_member(
        self, team_id: UUID, current_user_id: int, data: TeamMemberAdd
    ) -> TeamMemberResponse:
        db = self._get_db()
        actor = AuthorizationService(db).require_team_admin(team_id, current_user_id)
        if data.role == TeamRole.OWNER:
            raise ValidationError("Owner transfer is not supported by this operation")
        if data.role == TeamRole.ADMIN and actor.role != TeamRole.OWNER:
            raise AuthorizationError("Only a team owner may add an admin")
        user = db.query(User).filter(User.id == data.user_id, User.is_active.is_(True)).first()
        if user is None:
            raise NotFoundError("User not found")
        if AuthorizationService(db).team_membership(team_id, data.user_id) is not None:
            raise ConflictError("User is already a member of this team")
        membership = TeamMembership(team_id=team_id, user_id=data.user_id, role=data.role)
        db.add(membership)
        try:
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise ConflictError("User is already a member of this team") from error
        db.refresh(membership)
        return self._member_response(membership)

    def update_member_role(
        self,
        team_id: UUID,
        member_user_id: int,
        current_user_id: int,
        role: TeamRole,
    ) -> TeamMemberResponse:
        db = self._get_db()
        AuthorizationService(db).require_team_owner(team_id, current_user_id)
        membership = AuthorizationService(db).team_membership(team_id, member_user_id)
        if membership is None:
            raise NotFoundError("Team member not found")
        if membership.role == TeamRole.OWNER or role == TeamRole.OWNER:
            raise ValidationError("Owner transfer requires a dedicated safe operation")
        membership.role = role
        db.commit()
        db.refresh(membership)
        return self._member_response(membership)

    def remove_member(
        self, team_id: UUID, member_user_id: int, current_user_id: int
    ) -> None:
        db = self._get_db()
        actor = AuthorizationService(db).require_team_admin(team_id, current_user_id)
        membership = AuthorizationService(db).team_membership(team_id, member_user_id)
        if membership is None:
            raise NotFoundError("Team member not found")
        if membership.role == TeamRole.OWNER:
            raise ValidationError("The team owner cannot be removed")
        if membership.role == TeamRole.ADMIN and actor.role != TeamRole.OWNER:
            raise AuthorizationError("Only a team owner may remove an admin")

        project_ids = [
            project_id
            for project_id, in db.query(Project.id).filter(Project.team_id == team_id).all()
        ]
        if project_ids:
            db.query(ProjectMembership).filter(
                ProjectMembership.project_id.in_(project_ids),
                ProjectMembership.user_id == member_user_id,
            ).delete(synchronize_session=False)
        db.delete(membership)
        db.commit()
