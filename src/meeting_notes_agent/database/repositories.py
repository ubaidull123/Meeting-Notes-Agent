"""Database repositories for data access."""
from datetime import date, datetime, timezone
from typing import Optional, List, Tuple
import uuid
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, and_, or_, exists

from meeting_notes_agent.database.models import (
    User,
    UserQuota,
    UserCredits,
    UserUsage,
    Meeting,
    Attendee,
    Task,
    UserRole,
    MeetingStatus,
    TaskStatus,
    TaskPriority,
    ProjectMembership,
    TeamMembership,
    TeamRole,
)
from meeting_notes_agent.config.core.exceptions import NotFoundError, ConflictError


class UserRepository:
    """User repository for user data access."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, email: str, password_hash: str, full_name: str, role: UserRole = UserRole.USER) -> User:
        """Create a new user."""
        user = User(email=email.lower(), password_hash=password_hash, full_name=full_name, role=role)
        self.db.add(user)
        self.db.flush()
        return user

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        """Get all users with pagination and filters."""
        query = self.db.query(User)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                )
            )
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        total = query.count()
        users = query.order_by(desc(User.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        return users, total

    def count(self, is_active: Optional[bool] = None) -> int:
        """Count users."""
        query = self.db.query(User)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        return query.count()

    def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[User], int]:
        """Alias for get_all for admin service compatibility."""
        return self.get_all(page, page_size, search, role, is_active)

    def update(self, user: User, **kwargs) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            if hasattr(user, key) and key not in ("id", "email", "created_at", "password_hash"):
                setattr(user, key, value)
        user.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return user

    def update_password(self, user: User, password_hash: str) -> User:
        """Update user password hash."""
        user.password_hash = password_hash
        user.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        """Delete a user."""
        self.db.delete(user)
        self.db.flush()


class UserQuotaRepository:
    """User quota repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, user_id: int) -> UserQuota:
        """Get or create user quota."""
        quota = self.db.query(UserQuota).filter(UserQuota.user_id == user_id).first()
        if not quota:
            quota = UserQuota(user_id=user_id)
            self.db.add(quota)
            self.db.flush()
        return quota

    def get_by_user_id(self, user_id: int) -> Optional[UserQuota]:
        """Get quota by user ID."""
        return self.db.query(UserQuota).filter(UserQuota.user_id == user_id).first()

    def update(self, quota: UserQuota, **kwargs) -> UserQuota:
        """Update quota fields."""
        for key, value in kwargs.items():
            if hasattr(quota, key) and key not in ("user_id", "created_at"):
                setattr(quota, key, value)
        quota.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return quota

    def update_quota(self, quota: UserQuota, monthly_limit: int) -> UserQuota:
        """Update quota monthly limit."""
        quota.monthly_meeting_limit = monthly_limit
        quota.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return quota


class UserCreditsRepository:
    """User credits repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, user_id: int) -> UserCredits:
        """Get or create user credits."""
        credits = self.db.query(UserCredits).filter(UserCredits.user_id == user_id).first()
        if not credits:
            credits = UserCredits(user_id=user_id)
            self.db.add(credits)
            self.db.flush()
        return credits

    def get_by_user_id(self, user_id: int) -> Optional[UserCredits]:
        """Get credits by user ID."""
        return self.db.query(UserCredits).filter(UserCredits.user_id == user_id).first()

    def adjust_balance(self, user_id: int, amount: int) -> UserCredits:
        """Adjust credit balance (can be negative)."""
        credits = self.get_or_create(user_id)
        credits.balance += amount
        if credits.balance < 0:
            credits.balance = 0
        credits.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return credits

    def add_credits(self, credits: UserCredits, amount: int, reason: str) -> UserCredits:
        """Add credits to a user's balance."""
        credits.balance += amount
        credits.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return credits

    def deduct_credits(self, credits: UserCredits, amount: int, reason: str) -> UserCredits:
        """Deduct credits from a user's balance."""
        credits.balance = max(0, credits.balance - amount)
        credits.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return credits

    def sum_credits_issued(self) -> int:
        """Sum total credits issued across all users."""
        result = self.db.query(func.coalesce(func.sum(UserCredits.balance), 0)).scalar()
        return result or 0

    def sum_credits_consumed(self) -> int:
        """Sum total credits consumed across all users."""
        result = self.db.query(func.coalesce(func.sum(UserUsage.credits_consumed), 0)).scalar()
        return result or 0


class UserUsageRepository:
    """User usage repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_current_month(self, user_id: int) -> UserUsage:
        """Get or create usage record for current month."""
        month_start = date.today().replace(day=1)
        usage = self.db.query(UserUsage).filter(
            UserUsage.user_id == user_id,
            UserUsage.month == month_start
        ).first()
        if not usage:
            usage = UserUsage(user_id=user_id, month=month_start)
            self.db.add(usage)
            self.db.flush()
        return usage

    def get_current_month(self, user_id: int) -> Optional[UserUsage]:
        """Return the current month's usage without creating a new row."""
        month_start = date.today().replace(day=1)
        return self.db.query(UserUsage).filter(
            UserUsage.user_id == user_id,
            UserUsage.month == month_start,
        ).first()

    def get_by_user_id(self, user_id: int, limit: int = 12) -> List[UserUsage]:
        """Get usage history for user."""
        return self.db.query(UserUsage).filter(
            UserUsage.user_id == user_id
        ).order_by(desc(UserUsage.month)).limit(limit).all()

    def increment_usage(self, user_id: int, tokens_used: int) -> UserUsage:
        """Increment usage counters for current month."""
        usage = self.get_or_create_current_month(user_id)
        usage.meetings_processed += 1
        usage.tokens_used += tokens_used
        usage.credits_consumed += 1
        usage.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return usage


class MeetingRepository:
    """Meeting repository."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, meeting: Meeting) -> Meeting:
        """Create a new meeting."""
        self.db.add(meeting)
        self.db.flush()
        return meeting

    def get_by_id(self, meeting_id: UUID, user_id: Optional[int] = None) -> Optional[Meeting]:
        """Get a meeting only when the user has team/project access."""
        query = self.db.query(Meeting).filter(Meeting.id == meeting_id)
        if user_id is not None:
            query = (
                query.join(
                    TeamMembership,
                    TeamMembership.team_id == Meeting.team_id,
                )
                .outerjoin(
                    ProjectMembership,
                    and_(
                        ProjectMembership.project_id == Meeting.project_id,
                        ProjectMembership.user_id == user_id,
                    ),
                )
                .filter(
                    TeamMembership.user_id == user_id,
                    or_(
                        TeamMembership.role.in_([TeamRole.OWNER, TeamRole.ADMIN]),
                        and_(
                            or_(
                                Meeting.project_id.is_(None),
                                ProjectMembership.id.isnot(None),
                            ),
                            or_(
                                Meeting.restrict_to_participants.is_(False),
                                exists().where(
                                    and_(
                                        Attendee.meeting_id == Meeting.id,
                                        Attendee.user_id == user_id,
                                    )
                                ),
                            ),
                        ),
                    ),
                )
            )
        return query.first()

    def get_by_thread_id(self, thread_id: str) -> Optional[Meeting]:
        """Get meeting by LangGraph thread_id."""
        return self.db.query(Meeting).filter(Meeting.thread_id == thread_id).first()

    def get_user_meetings(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[MeetingStatus] = None,
        team_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> Tuple[List[Meeting], int]:
        """Get meetings visible through team and project membership."""
        query = (
            self.db.query(Meeting)
            .join(TeamMembership, TeamMembership.team_id == Meeting.team_id)
            .outerjoin(
                ProjectMembership,
                and_(
                    ProjectMembership.project_id == Meeting.project_id,
                    ProjectMembership.user_id == user_id,
                ),
            )
            .filter(
                TeamMembership.user_id == user_id,
                or_(
                    TeamMembership.role.in_([TeamRole.OWNER, TeamRole.ADMIN]),
                    and_(
                        or_(
                            Meeting.project_id.is_(None),
                            ProjectMembership.id.isnot(None),
                        ),
                        or_(
                            Meeting.restrict_to_participants.is_(False),
                            exists().where(
                                and_(
                                    Attendee.meeting_id == Meeting.id,
                                    Attendee.user_id == user_id,
                                )
                            ),
                        ),
                    ),
                ),
            )
        )
        if status:
            query = query.filter(Meeting.status == status)
        if team_id:
            query = query.filter(Meeting.team_id == team_id)
        if project_id:
            query = query.filter(Meeting.project_id == project_id)
        total = query.count()
        meetings = query.order_by(desc(Meeting.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        return meetings, total

    def get_all_meetings(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[MeetingStatus] = None,
        user_id: Optional[int] = None,
    ) -> Tuple[List[Meeting], int]:
        """Get all meetings (admin) with pagination."""
        query = self.db.query(Meeting).options(joinedload(Meeting.user))
        if status:
            query = query.filter(Meeting.status == status)
        if user_id:
            query = query.filter(Meeting.user_id == user_id)
        total = query.count()
        meetings = query.order_by(desc(Meeting.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        return meetings, total

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[MeetingStatus] = None,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Tuple[List[Meeting], int]:
        """Alias for get_all_meetings for admin service compatibility."""
        query = self.db.query(Meeting).options(joinedload(Meeting.user))
        if status:
            query = query.filter(Meeting.status == status)
        if user_id:
            query = query.filter(Meeting.user_id == user_id)
        if date_from:
            query = query.filter(Meeting.created_at >= date_from)
        if date_to:
            query = query.filter(Meeting.created_at <= date_to)
        total = query.count()
        meetings = query.order_by(desc(Meeting.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        return meetings, total

    def get_by_id_admin(self, meeting_id: UUID) -> Optional[Meeting]:
        """Get meeting by ID with user loaded (admin)."""
        return self.db.query(Meeting).options(joinedload(Meeting.user)).filter(Meeting.id == meeting_id).first()

    def update(self, meeting: Meeting, **kwargs) -> Meeting:
        """Update meeting fields."""
        for key, value in kwargs.items():
            if hasattr(meeting, key) and key not in ("id", "user_id", "created_at"):
                setattr(meeting, key, value)
        meeting.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return meeting

    def delete(self, meeting: Meeting) -> None:
        """Delete a meeting."""
        self.db.delete(meeting)
        self.db.flush()

    def count_by_user_and_month(self, user_id: int, month_start: date) -> int:
        """Count meetings for user in a given month."""
        return self.db.query(Meeting).filter(
            Meeting.user_id == user_id,
            func.date(Meeting.created_at) >= month_start,
        ).count()

    def count(self, status: Optional[MeetingStatus] = None, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> int:
        """Count meetings with optional filters."""
        query = self.db.query(Meeting)
        if status:
            query = query.filter(Meeting.status == status)
        if date_from:
            query = query.filter(Meeting.created_at >= date_from)
        if date_to:
            query = query.filter(Meeting.created_at <= date_to)
        return query.count()

    def sum_tokens(self) -> int:
        """Sum tokens used across all meetings."""
        result = self.db.query(func.coalesce(func.sum(Meeting.tokens_used), 0)).scalar()
        return result or 0

    def count_emails_sent(self) -> int:
        """Count meetings with emails sent."""
        return self.db.query(Meeting).filter(Meeting.email_sent == True).count()

    def count_user_meetings_this_month(self, user_id: int) -> int:
        """Count meetings for user in current month."""
        month_start = date.today().replace(day=1)
        return self.count_by_user_and_month(user_id, month_start)


class AttendeeRepository:
    """Attendee repository."""

    def __init__(self, db: Session):
        self.db = db

    def create_batch(self, meeting_id: UUID, attendees: List[dict]) -> List[Attendee]:
        """Create multiple attendees for a meeting."""
        attendee_objects = [
            Attendee(
                meeting_id=meeting_id,
                user_id=a.get("user_id"),
                name=a["name"],
                email=a["email"],
                title=a.get("title"),
                department=a.get("department"),
            )
            for a in attendees
        ]
        self.db.add_all(attendee_objects)
        self.db.flush()
        return attendee_objects

    def get_by_meeting_id(self, meeting_id: UUID) -> List[Attendee]:
        """Get all attendees for a meeting."""
        return self.db.query(Attendee).filter(Attendee.meeting_id == meeting_id).all()

    def delete_by_meeting_id(self, meeting_id: UUID) -> None:
        """Delete all attendees for a meeting."""
        self.db.query(Attendee).filter(Attendee.meeting_id == meeting_id).delete()
        self.db.flush()


class TaskRepository:
    """Task repository."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        meeting_id: UUID,
        meeting_title: str,
        action_item_index: int,
        title: str,
        description: Optional[str] = None,
        status: TaskStatus = TaskStatus.TODO,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assignee: Optional[str] = None,
        assigned_user_id: Optional[int] = None,
        due_date: Optional[date] = None,
        labels: Optional[List[str]] = None,
    ) -> Task:
        """Create a task for a meeting owned by the user."""
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            raise NotFoundError("Meeting not found")

        task = Task(
            id=str(uuid.uuid4())[:8],
            meeting_id=meeting_id,
            team_id=meeting.team_id,
            project_id=meeting.project_id,
            assigned_user_id=assigned_user_id,
            meeting_title=meeting_title,
            action_item_index=action_item_index,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee=assignee,
            due_date=due_date,
            labels=labels or ["meeting-action-item"],
        )
        self.db.add(task)
        self.db.flush()
        return task

    def create_batch(self, tasks: List[Task]) -> List[Task]:
        """Create multiple tasks."""
        self.db.add_all(tasks)
        self.db.flush()
        return tasks

    def get_by_id(self, task_id: str, user_id: Optional[int] = None) -> Optional[Task]:
        """Get a task only when team/project/assignment access permits it."""
        query = self.db.query(Task).filter(Task.id == task_id)
        if user_id is not None:
            query = (
                query.join(
                    TeamMembership,
                    TeamMembership.team_id == Task.team_id,
                )
                .outerjoin(
                    ProjectMembership,
                    and_(
                        ProjectMembership.project_id == Task.project_id,
                        ProjectMembership.user_id == user_id,
                    ),
                )
                .filter(
                    TeamMembership.user_id == user_id,
                    or_(
                        TeamMembership.role.in_([TeamRole.OWNER, TeamRole.ADMIN]),
                        Task.assigned_user_id == user_id,
                        ProjectMembership.id.isnot(None),
                    ),
                )
            )
        return query.first()

    def get_by_meeting_id(self, meeting_id: UUID, user_id: Optional[int] = None) -> List[Task]:
        """Get all tasks for a meeting."""
        query = self.db.query(Task).filter(Task.meeting_id == meeting_id)
        if user_id is not None:
            query = (
                query.join(
                    TeamMembership,
                    TeamMembership.team_id == Task.team_id,
                )
                .outerjoin(
                    ProjectMembership,
                    and_(
                        ProjectMembership.project_id == Task.project_id,
                        ProjectMembership.user_id == user_id,
                    ),
                )
                .filter(
                    TeamMembership.user_id == user_id,
                    or_(
                        TeamMembership.role.in_([TeamRole.OWNER, TeamRole.ADMIN]),
                        Task.assigned_user_id == user_id,
                        ProjectMembership.id.isnot(None),
                    ),
                )
            )
        return query.all()

    def get_by_meeting_and_action_item(self, meeting_id: UUID, action_item_index: int) -> Optional[Task]:
        """Get a task generated from a specific action item index."""
        return self.db.query(Task).filter(
            Task.meeting_id == meeting_id,
            Task.action_item_index == action_item_index,
        ).first()

    def get_user_tasks(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        meeting_id: Optional[UUID] = None,
        status: Optional[TaskStatus] = None,
        team_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
    ) -> Tuple[List[Task], int]:
        """Get user's tasks with pagination."""
        query = (
            self.db.query(Task)
            .join(TeamMembership, TeamMembership.team_id == Task.team_id)
            .outerjoin(
                ProjectMembership,
                and_(
                    ProjectMembership.project_id == Task.project_id,
                    ProjectMembership.user_id == user_id,
                ),
            )
            .filter(
                TeamMembership.user_id == user_id,
                or_(
                    TeamMembership.role.in_([TeamRole.OWNER, TeamRole.ADMIN]),
                    Task.assigned_user_id == user_id,
                    ProjectMembership.id.isnot(None),
                ),
            )
        )
        if meeting_id:
            query = query.filter(Task.meeting_id == meeting_id)
        if status:
            query = query.filter(Task.status == status)
        if team_id:
            query = query.filter(Task.team_id == team_id)
        if project_id:
            query = query.filter(Task.project_id == project_id)
        total = query.count()
        tasks = query.order_by(desc(Task.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        return tasks, total

    def update(self, task: Task, **kwargs) -> Task:
        """Update task fields."""
        for key, value in kwargs.items():
            if hasattr(task, key) and key not in ("id", "meeting_id", "meeting_title", "action_item_index", "created_at"):
                setattr(task, key, value)
        task.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return task

    def delete(self, task: Task) -> None:
        """Delete a task."""
        self.db.delete(task)
        self.db.flush()

    def delete_by_meeting_id(self, meeting_id: UUID) -> None:
        """Delete all tasks for a meeting."""
        self.db.query(Task).filter(Task.meeting_id == meeting_id).delete()
        self.db.flush()
