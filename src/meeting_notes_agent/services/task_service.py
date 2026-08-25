"""Task service."""
from datetime import date, datetime
from typing import Optional, List, Tuple
from uuid import UUID

from meeting_notes_agent.database import TaskRepository, get_db
from meeting_notes_agent.database.models import TaskStatus, TaskPriority, TeamRole
from meeting_notes_agent.config.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from meeting_notes_agent.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from meeting_notes_agent.services.authorization_service import AuthorizationService


class TaskService:
    """Service for task operations."""

    def __init__(self, db=None):
        self.db = db

    def _get_db(self):
        """Get database session."""
        if self.db:
            return self.db
        return next(get_db())

    def create_task(self, user_id: int, data: TaskCreate) -> TaskResponse:
        """Create a new task."""
        db = self._get_db()
        task_repo = TaskRepository(db)
        authorization = AuthorizationService(db)
        meeting = authorization.require_meeting_admin(data.meeting_id, user_id)
        assigned_user = authorization.validate_task_assignee(
            team_id=meeting.team_id,
            project_id=meeting.project_id,
            assigned_user_id=data.assigned_user_id,
        )

        task = task_repo.create(
            user_id=user_id,
            meeting_id=data.meeting_id,
            meeting_title=data.meeting_title,
            action_item_index=data.action_item_index,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            assignee=assigned_user.full_name if assigned_user else data.assignee,
            assigned_user_id=data.assigned_user_id,
            due_date=data.due_date,
            labels=data.labels,
        )

        db.commit()
        db.refresh(task)
        return TaskResponse.model_validate(task)

    def get_task(self, task_id: str, user_id: int) -> TaskResponse:
        """Get task by ID."""
        db = self._get_db()
        task_repo = TaskRepository(db)

        task = AuthorizationService(db).require_task_access(task_id, user_id)
        return TaskResponse.model_validate(task)

    def list_tasks(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        meeting_id: Optional[UUID] = None,
        status: Optional[TaskStatus] = None,
        team_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> TaskListResponse:
        """List user's tasks with optional filters."""
        db = self._get_db()
        task_repo = TaskRepository(db)

        tasks, total = task_repo.get_user_tasks(
            user_id=user_id,
            page=page,
            page_size=page_size,
            meeting_id=meeting_id,
            status=status,
            team_id=team_id,
            project_id=project_id,
        )
        return TaskListResponse(
            tasks=[TaskResponse.model_validate(t) for t in tasks],
            total=total,
            page=page,
            page_size=page_size,
        )

    def update_task(self, task_id: str, user_id: int, data: TaskUpdate) -> TaskResponse:
        """Update a task."""
        db = self._get_db()
        task_repo = TaskRepository(db)

        update_data = data.model_dump(exclude_unset=True)
        authorization = AuthorizationService(db)
        task = authorization.require_task_access(task_id, user_id)
        membership = authorization.require_team_member(task.team_id, user_id)
        if membership.role not in {TeamRole.OWNER, TeamRole.ADMIN}:
            if set(update_data) - {"status"}:
                raise AuthorizationError("Members may update only task status")
            task = authorization.require_task_status_access(task_id, user_id)
        if "assigned_user_id" in update_data:
            assigned_user = authorization.validate_task_assignee(
                team_id=task.team_id,
                project_id=task.project_id,
                assigned_user_id=update_data["assigned_user_id"],
            )
            update_data["assignee"] = assigned_user.full_name if assigned_user else None
        task_repo.update(task, **update_data)
        db.commit()
        db.refresh(task)

        return TaskResponse.model_validate(task)

    def delete_task(self, task_id: str, user_id: int) -> None:
        """Delete a task."""
        db = self._get_db()
        task_repo = TaskRepository(db)

        task = AuthorizationService(db).require_task_admin(task_id, user_id)

        task_repo.delete(task)
        db.commit()

    def mark_task_complete(self, task_id: str, user_id: int) -> TaskResponse:
        """Mark task as complete."""
        db = self._get_db()
        task_repo = TaskRepository(db)

        task = AuthorizationService(db).require_task_status_access(task_id, user_id)

        task_repo.update(task, status=TaskStatus.DONE)
        db.commit()
        db.refresh(task)

        return TaskResponse.model_validate(task)

    def sync_tasks_from_meeting(self, user_id: int, meeting_id: UUID, action_items: List[dict]) -> List[TaskResponse]:
        """Sync tasks from meeting action items."""
        db = self._get_db()
        task_repo = TaskRepository(db)

        created_tasks = []
        for idx, item in enumerate(action_items):
            # Check if task already exists for this action item
            existing = task_repo.get_by_meeting_and_action_item(meeting_id, idx)
            if existing:
                # Update existing task
                task_repo.update(
                    existing,
                    title=item.get("title", f"Action Item {idx + 1}"),
                    description=item.get("description"),
                    status=TaskStatus.TODO,
                    priority=TaskPriority.MEDIUM,
                    assignee=item.get("assignee"),
                    due_date=item.get("due_date"),
                    labels=item.get("labels", ["meeting-action-item"]),
                )
                db.commit()
                db.refresh(existing)
                created_tasks.append(TaskResponse.model_validate(existing))
            else:
                # Create new task
                task = task_repo.create(
                    user_id=user_id,
                    meeting_id=meeting_id,
                    meeting_title=item.get("meeting_title", "Meeting"),
                    action_item_index=idx,
                    title=item.get("title", f"Action Item {idx + 1}"),
                    description=item.get("description"),
                    status=TaskStatus.TODO,
                    priority=TaskPriority.MEDIUM,
                    assignee=item.get("assignee"),
                    due_date=item.get("due_date"),
                    labels=item.get("labels", ["meeting-action-item"]),
                )
                created_tasks.append(TaskResponse.model_validate(task))

        db.commit()
        return created_tasks
