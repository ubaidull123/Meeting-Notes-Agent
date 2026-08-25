"""Centralized team, project, meeting, and task authorization."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from meeting_notes_agent.config.core.exceptions import (
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from meeting_notes_agent.database.models import (
    Attendee,
    Meeting,
    Project,
    ProjectMembership,
    Task,
    TeamMembership,
    TeamRole,
    User,
)


TEAM_MANAGEMENT_ROLES = {TeamRole.OWNER, TeamRole.ADMIN}


class AuthorizationService:
    """Single source of truth for tenant-scoped permission checks."""

    def __init__(self, db: Session):
        self.db = db

    def team_membership(self, team_id: UUID, user_id: int) -> TeamMembership | None:
        return (
            self.db.query(TeamMembership)
            .filter(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == user_id,
            )
            .first()
        )

    def require_team_member(self, team_id: UUID, user_id: int) -> TeamMembership:
        membership = self.team_membership(team_id, user_id)
        if membership is None:
            raise AuthorizationError("Team membership required")
        return membership

    def require_team_admin(self, team_id: UUID, user_id: int) -> TeamMembership:
        membership = self.require_team_member(team_id, user_id)
        if membership.role not in TEAM_MANAGEMENT_ROLES:
            raise AuthorizationError("Team owner or admin access required")
        return membership

    def require_team_owner(self, team_id: UUID, user_id: int) -> TeamMembership:
        membership = self.require_team_member(team_id, user_id)
        if membership.role != TeamRole.OWNER:
            raise AuthorizationError("Team owner access required")
        return membership

    def require_project_member(self, project_id: UUID, user_id: int) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project is None:
            raise NotFoundError("Project not found")
        team_membership = self.team_membership(project.team_id, user_id)
        if team_membership is None:
            raise NotFoundError("Project not found")
        if team_membership.role in TEAM_MANAGEMENT_ROLES:
            return project
        membership = (
            self.db.query(ProjectMembership)
            .filter(
                ProjectMembership.project_id == project.id,
                ProjectMembership.user_id == user_id,
            )
            .first()
        )
        if membership is None:
            raise NotFoundError("Project not found")
        return project

    def require_project_access(self, project_id: UUID, user_id: int) -> Project:
        return self.require_project_member(project_id, user_id)

    def require_project_admin(self, project_id: UUID, user_id: int) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if project is None:
            raise NotFoundError("Project not found")
        try:
            self.require_team_admin(project.team_id, user_id)
        except AuthorizationError as error:
            raise NotFoundError("Project not found") from error
        return project

    def require_meeting_access(self, meeting_id: UUID, user_id: int) -> Meeting:
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting is None:
            raise NotFoundError("Meeting not found")
        team_membership = self.team_membership(meeting.team_id, user_id)
        if team_membership is None:
            raise NotFoundError("Meeting not found")
        if team_membership.role in TEAM_MANAGEMENT_ROLES or meeting.project_id is None:
            if team_membership.role in TEAM_MANAGEMENT_ROLES:
                return meeting
        if meeting.project_id is not None:
            project_membership = (
                self.db.query(ProjectMembership)
                .filter(
                    ProjectMembership.project_id == meeting.project_id,
                    ProjectMembership.user_id == user_id,
                )
                .first()
            )
            if project_membership is None:
                raise NotFoundError("Meeting not found")
        if meeting.restrict_to_participants:
            participant = (
                self.db.query(Attendee)
                .filter(
                    Attendee.meeting_id == meeting.id,
                    Attendee.user_id == user_id,
                )
                .first()
            )
            if participant is None:
                raise NotFoundError("Meeting not found")
        return meeting

    def require_meeting_admin(self, meeting_id: UUID, user_id: int) -> Meeting:
        meeting = self.require_meeting_access(meeting_id, user_id)
        try:
            self.require_team_admin(meeting.team_id, user_id)
        except AuthorizationError as error:
            raise AuthorizationError("Only team owners and admins may manage meetings") from error
        return meeting

    def require_task_access(self, task_id: str, user_id: int) -> Task:
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if task is None:
            raise NotFoundError("Task not found")
        team_membership = self.team_membership(task.team_id, user_id)
        if team_membership is None:
            raise NotFoundError("Task not found")
        if team_membership.role in TEAM_MANAGEMENT_ROLES:
            return task
        if task.assigned_user_id == user_id:
            return task
        if task.project_id is not None:
            project_membership = (
                self.db.query(ProjectMembership)
                .filter(
                    ProjectMembership.project_id == task.project_id,
                    ProjectMembership.user_id == user_id,
                )
                .first()
            )
            if project_membership is not None:
                return task
        raise NotFoundError("Task not found")

    def require_task_status_access(self, task_id: str, user_id: int) -> Task:
        task = self.require_task_access(task_id, user_id)
        membership = self.require_team_member(task.team_id, user_id)
        if membership.role in TEAM_MANAGEMENT_ROLES or task.assigned_user_id == user_id:
            return task
        raise AuthorizationError("Only the assignee or a team admin may update task status")

    def require_task_admin(self, task_id: str, user_id: int) -> Task:
        task = self.require_task_access(task_id, user_id)
        self.require_team_admin(task.team_id, user_id)
        return task

    def validate_task_assignee(
        self,
        *,
        team_id: UUID,
        project_id: UUID | None,
        assigned_user_id: int | None,
    ) -> User | None:
        if assigned_user_id is None:
            return None
        user = self.db.query(User).filter(User.id == assigned_user_id).first()
        if user is None or not user.is_active:
            raise ValidationError("Task assignee does not exist or is inactive")
        if self.team_membership(team_id, assigned_user_id) is None:
            raise ValidationError("Task assignee must belong to the team")
        if project_id is not None:
            project_membership = (
                self.db.query(ProjectMembership)
                .filter(
                    ProjectMembership.project_id == project_id,
                    ProjectMembership.user_id == assigned_user_id,
                )
                .first()
            )
            if project_membership is None:
                raise ValidationError("Task assignee must belong to the project")
        return user
