"""Team-scoped project and project-membership operations."""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from meeting_notes_agent.config.core.exceptions import ConflictError, NotFoundError
from meeting_notes_agent.database import get_db
from meeting_notes_agent.database.models import (
    Project,
    ProjectMembership,
    TeamMembership,
    User,
)
from meeting_notes_agent.schemas.project import (
    ProjectCreate,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)
from meeting_notes_agent.services.authorization_service import AuthorizationService


def normalize_project_name(value: str) -> tuple[str, str]:
    display = re.sub(r"\s+", " ", value.strip())
    return display, display.casefold()


class ProjectService:
    def __init__(self, db=None):
        self.db = db

    def _get_db(self):
        return self.db or next(get_db())

    @staticmethod
    def _member_response(membership: ProjectMembership) -> ProjectMemberResponse:
        return ProjectMemberResponse(
            id=membership.id,
            project_id=membership.project_id,
            user_id=membership.user_id,
            email=membership.user.email,
            full_name=membership.user.full_name,
            is_active=membership.user.is_active,
            created_at=membership.created_at,
        )

    def create_project(
        self, team_id: UUID, user_id: int, data: ProjectCreate
    ) -> ProjectResponse:
        db = self._get_db()
        AuthorizationService(db).require_team_admin(team_id, user_id)
        name, normalized_name = normalize_project_name(data.name)
        project = Project(
            team_id=team_id,
            name=name,
            normalized_name=normalized_name,
            description=data.description,
            context=data.context,
            created_by=user_id,
        )
        db.add(project)
        try:
            db.flush()
            member_ids = set(data.member_ids)
            member_ids.add(user_id)
            team_member_ids = {
                member_id
                for member_id, in db.query(TeamMembership.user_id)
                .filter(
                    TeamMembership.team_id == team_id,
                    TeamMembership.user_id.in_(member_ids),
                )
                .all()
            }
            missing = member_ids - team_member_ids
            if missing:
                raise NotFoundError("Every project member must belong to the team")
            db.add_all(
                [
                    ProjectMembership(project_id=project.id, user_id=member_id)
                    for member_id in sorted(member_ids)
                ]
            )
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise ConflictError("A project with this name already exists in the team") from error
        except Exception:
            db.rollback()
            raise
        db.refresh(project)
        return ProjectResponse.model_validate(project)

    def list_projects(self, team_id: UUID, user_id: int) -> list[ProjectResponse]:
        db = self._get_db()
        team_membership = AuthorizationService(db).require_team_member(team_id, user_id)
        query = db.query(Project).filter(Project.team_id == team_id)
        if team_membership.role.value == "member":
            query = query.join(ProjectMembership).filter(
                ProjectMembership.user_id == user_id
            )
        projects = query.order_by(Project.name.asc()).all()
        return [ProjectResponse.model_validate(project) for project in projects]

    def get_project(self, project_id: UUID, user_id: int) -> ProjectResponse:
        db = self._get_db()
        project = AuthorizationService(db).require_project_access(project_id, user_id)
        return ProjectResponse.model_validate(project)

    def update_project(
        self, project_id: UUID, user_id: int, data: ProjectUpdate
    ) -> ProjectResponse:
        db = self._get_db()
        project = AuthorizationService(db).require_project_admin(project_id, user_id)
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes:
            changes["name"], changes["normalized_name"] = normalize_project_name(
                changes["name"]
            )
        for field, value in changes.items():
            setattr(project, field, value)
        try:
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise ConflictError("A project with this name already exists in the team") from error
        db.refresh(project)
        return ProjectResponse.model_validate(project)

    def delete_project(self, project_id: UUID, user_id: int) -> None:
        db = self._get_db()
        project = AuthorizationService(db).require_project_admin(project_id, user_id)
        db.delete(project)
        db.commit()

    def list_members(
        self, project_id: UUID, user_id: int
    ) -> list[ProjectMemberResponse]:
        db = self._get_db()
        AuthorizationService(db).require_project_access(project_id, user_id)
        memberships = (
            db.query(ProjectMembership)
            .join(User)
            .filter(ProjectMembership.project_id == project_id)
            .order_by(User.full_name.asc())
            .all()
        )
        return [self._member_response(item) for item in memberships]

    def add_member(
        self, project_id: UUID, member_user_id: int, current_user_id: int
    ) -> ProjectMemberResponse:
        db = self._get_db()
        project = AuthorizationService(db).require_project_admin(
            project_id, current_user_id
        )
        if AuthorizationService(db).team_membership(project.team_id, member_user_id) is None:
            raise NotFoundError("User must belong to the project team")
        existing = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.project_id == project_id,
                ProjectMembership.user_id == member_user_id,
            )
            .first()
        )
        if existing is not None:
            raise ConflictError("User is already a project member")
        membership = ProjectMembership(
            project_id=project_id, user_id=member_user_id
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return self._member_response(membership)

    def remove_member(
        self, project_id: UUID, member_user_id: int, current_user_id: int
    ) -> None:
        db = self._get_db()
        AuthorizationService(db).require_project_admin(project_id, current_user_id)
        membership = (
            db.query(ProjectMembership)
            .filter(
                ProjectMembership.project_id == project_id,
                ProjectMembership.user_id == member_user_id,
            )
            .first()
        )
        if membership is None:
            raise NotFoundError("Project member not found")
        db.delete(membership)
        db.commit()
