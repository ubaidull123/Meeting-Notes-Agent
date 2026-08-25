"""Transactional team and team-membership operations."""

from __future__ import annotations

from datetime import datetime, timezone
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
    TeamInvitation,
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
            title=membership.title,
            department=membership.department,
            status="active",
            is_active=membership.user.is_active,
            accepted_at=membership.created_at,
            created_at=membership.created_at,
            updated_at=membership.updated_at,
        )

    @staticmethod
    def _invitation_response(invitation: TeamInvitation) -> TeamMemberResponse:
        return TeamMemberResponse(
            id=invitation.id,
            team_id=invitation.team_id,
            user_id=None,
            role=invitation.role,
            email=invitation.email,
            full_name=invitation.full_name,
            title=invitation.title,
            department=invitation.department,
            status=invitation.status,
            is_active=False,
            accepted_at=invitation.accepted_at,
            created_at=invitation.created_at,
            updated_at=invitation.updated_at,
        )

    def create_team(self, user_id: int, data: TeamCreate) -> TeamListItem:
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
        return TeamListItem(
            id=team.id,
            name=team.name,
            description=team.description,
            role=TeamRole.OWNER,
            created_by=team.created_by,
            created_at=team.created_at,
            updated_at=team.updated_at,
        )

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
        invitations = (
            db.query(TeamInvitation)
            .filter(
                TeamInvitation.team_id == team_id,
                TeamInvitation.status == "pending",
            )
            .order_by(TeamInvitation.full_name.asc())
            .all()
        )
        return [
            *[self._member_response(item) for item in memberships],
            *[self._invitation_response(item) for item in invitations],
        ]

    def add_member(
        self, team_id: UUID, current_user_id: int, data: TeamMemberAdd
    ) -> TeamMemberResponse:
        db = self._get_db()
        actor = AuthorizationService(db).require_team_admin(team_id, current_user_id)
        if data.role == TeamRole.OWNER:
            raise ValidationError("Owner transfer is not supported by this operation")
        if data.role == TeamRole.ADMIN and actor.role != TeamRole.OWNER:
            raise AuthorizationError("Only a team owner may add an admin")
        legacy_user = (
            db.query(User)
            .filter(User.id == data.user_id, User.is_active.is_(True))
            .first()
            if data.user_id is not None
            else None
        )
        if data.user_id is not None and legacy_user is None:
            raise NotFoundError("User not found")
        email = (legacy_user.email if legacy_user else str(data.email)).strip().lower()
        full_name = (legacy_user.full_name if legacy_user else str(data.full_name)).strip()
        title = data.title.strip() if data.title and data.title.strip() else None
        department = (
            data.department.strip() if data.department and data.department.strip() else None
        )
        user = legacy_user or db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
        existing_invitation = (
            db.query(TeamInvitation)
            .filter(TeamInvitation.team_id == team_id, TeamInvitation.email == email)
            .first()
        )
        if user is not None:
            if AuthorizationService(db).team_membership(team_id, user.id) is not None:
                raise ConflictError("This email is already a member of the team")
            membership = TeamMembership(
                team_id=team_id,
                user_id=user.id,
                role=data.role,
                title=title,
                department=department,
            )
            db.add(membership)
            if existing_invitation is not None:
                existing_invitation.status = "accepted"
                existing_invitation.accepted_by = user.id
                existing_invitation.accepted_at = datetime.now(timezone.utc)
            try:
                db.commit()
            except IntegrityError as error:
                db.rollback()
                raise ConflictError("This email is already a member of the team") from error
            db.refresh(membership)
            return self._member_response(membership)

        if existing_invitation is not None:
            if existing_invitation.status == "pending":
                raise ConflictError("An invitation for this email is already pending")
            existing_invitation.full_name = full_name
            existing_invitation.title = title
            existing_invitation.department = department
            existing_invitation.role = data.role
            existing_invitation.status = "pending"
            existing_invitation.invited_by = current_user_id
            existing_invitation.accepted_by = None
            existing_invitation.accepted_at = None
            invitation = existing_invitation
        else:
            invitation = TeamInvitation(
                team_id=team_id,
                email=email,
                full_name=full_name,
                title=title,
                department=department,
                role=data.role,
                status="pending",
                invited_by=current_user_id,
            )
            db.add(invitation)
        try:
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise ConflictError("An invitation for this email already exists") from error
        db.refresh(invitation)
        return self._invitation_response(invitation)

    def revoke_invitation(
        self, team_id: UUID, invitation_id: UUID, current_user_id: int
    ) -> None:
        db = self._get_db()
        AuthorizationService(db).require_team_admin(team_id, current_user_id)
        invitation = (
            db.query(TeamInvitation)
            .filter(
                TeamInvitation.id == invitation_id,
                TeamInvitation.team_id == team_id,
                TeamInvitation.status == "pending",
            )
            .first()
        )
        if invitation is None:
            raise NotFoundError("Invitation not found")
        invitation.status = "revoked"
        db.commit()

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
