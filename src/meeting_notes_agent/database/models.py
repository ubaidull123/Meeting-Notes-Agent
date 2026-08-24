"""SQLAlchemy database models for the Meeting Notes API."""
import uuid
from datetime import date, datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    String,
    Text,
    Date,
    DateTime,
    Integer,
    ForeignKey,
    Boolean,
    Index,
    UniqueConstraint,
    JSON,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class UserRole(str, PyEnum):
    """User roles."""
    USER = "USER"
    ADMIN = "ADMIN"


class PlatformRole(str, PyEnum):
    """Platform-wide SaaS authority, separate from team membership roles."""

    USER = "user"
    PLATFORM_ADMIN = "platform_admin"


class TeamRole(str, PyEnum):
    """Authority within one team workspace."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class TaskStatus(str, PyEnum):
    """Task status options."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(str, PyEnum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MeetingStatus(str, PyEnum):
    """Meeting processing status."""
    DRAFT = "draft"
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    REVISION_REQUESTED = "revision_requested"
    AWAITING_EMAIL_REVIEW = "awaiting_email_review"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(SQLEnum(UserRole, native_enum=False), default=UserRole.USER, nullable=False)
    platform_role = Column(
        SQLEnum(PlatformRole, native_enum=False),
        default=PlatformRole.USER,
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    meetings = relationship(
        "Meeting",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Meeting.user_id",
    )
    quotas = relationship("UserQuota", back_populates="user", uselist=False, cascade="all, delete-orphan")
    credits = relationship("UserCredits", back_populates="user", uselist=False, cascade="all, delete-orphan")
    usage_records = relationship("UserUsage", back_populates="user", cascade="all, delete-orphan")
    ai_config = relationship("UserAIConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    credentials = relationship("UserCredential", back_populates="user", cascade="all, delete-orphan")
    email_config = relationship("UserEmailConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    product_settings = relationship("UserProductSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", backref="user", lazy="dynamic")
    usage_records_new = relationship("UsageRecord", backref="user", lazy="dynamic")
    ai_overrides = relationship("MeetingAIOverride", back_populates="user", lazy="dynamic")
    teams_created = relationship(
        "Team", back_populates="creator", foreign_keys="Team.created_by"
    )
    team_memberships = relationship(
        "TeamMembership", back_populates="user", cascade="all, delete-orphan"
    )
    projects_created = relationship(
        "Project", back_populates="creator", foreign_keys="Project.created_by"
    )
    project_memberships = relationship(
        "ProjectMembership", back_populates="user", cascade="all, delete-orphan"
    )
    meetings_created = relationship(
        "Meeting", back_populates="creator", foreign_keys="Meeting.created_by"
    )
    assigned_tasks = relationship(
        "Task", back_populates="assigned_user", foreign_keys="Task.assigned_user_id"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"


class UserQuota(Base):
    """User monthly quota model."""
    __tablename__ = "user_quotas"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    monthly_meeting_limit = Column(Integer, default=20, nullable=False)
    monthly_credits = Column(Integer, default=500, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="quotas")

    def __repr__(self) -> str:
        return f"<UserQuota(user_id={self.user_id}, limit={self.monthly_meeting_limit}, credits={self.monthly_credits})>"


class UserCredits(Base):
    """User credits balance model."""
    __tablename__ = "user_credits"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    balance = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="credits")

    def __repr__(self) -> str:
        return f"<UserCredits(user_id={self.user_id}, balance={self.balance})>"


class UserUsage(Base):
    """User monthly usage tracking model."""
    __tablename__ = "user_usage"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    month = Column(Date, nullable=False, index=True)  # First day of month
    meetings_processed = Column(Integer, default=0, nullable=False)
    tokens_used = Column(Integer, default=0, nullable=False)
    credits_consumed = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="usage_records")

    __table_args__ = (
        UniqueConstraint("user_id", "month", name="uq_user_usage_user_month"),
        Index("idx_user_usage_user_month_desc", "user_id", "month", postgresql_using="btree"),
    )

    def __repr__(self) -> str:
        return f"<UserUsage(user_id={self.user_id}, month={self.month}, meetings={self.meetings_processed})>"


class Team(Base):
    """Organizational workspace containing projects and meetings."""

    __tablename__ = "teams"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    creator = relationship("User", back_populates="teams_created", foreign_keys=[created_by])
    memberships = relationship(
        "TeamMembership", back_populates="team", cascade="all, delete-orphan"
    )
    projects = relationship("Project", back_populates="team", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="team")
    tasks = relationship("Task", back_populates="team")


class TeamMembership(Base):
    """A user's role within one team."""

    __tablename__ = "team_memberships"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(SQLEnum(TeamRole, native_enum=False), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    team = relationship("Team", back_populates="memberships")
    user = relationship("User", back_populates="team_memberships")

    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_membership_team_user"),
    )


class Project(Base):
    """Team-scoped project with reusable context for meeting processing."""

    __tablename__ = "projects"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    team = relationship("Team", back_populates="projects")
    creator = relationship("User", back_populates="projects_created", foreign_keys=[created_by])
    memberships = relationship(
        "ProjectMembership", back_populates="project", cascade="all, delete-orphan"
    )
    meetings = relationship("Meeting", back_populates="project")
    tasks = relationship("Task", back_populates="project")

    __table_args__ = (
        UniqueConstraint("team_id", "normalized_name", name="uq_project_team_normalized_name"),
        Index("idx_projects_team_name", "team_id", "name"),
    )


class ProjectMembership(Base):
    """Explicit user access to a project within its team."""

    __tablename__ = "project_memberships"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    project = relationship("Project", back_populates="memberships")
    user = relationship("User", back_populates="project_memberships")

    __table_args__ = (
        UniqueConstraint(
            "project_id", "user_id", name="uq_project_membership_project_user"
        ),
    )


class Meeting(Base):
    """Meeting model."""
    __tablename__ = "meetings"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title = Column(String(500), nullable=False)
    meeting_date = Column(Date, nullable=False)
    meeting_time = Column(String(50), nullable=True)
    project_name = Column(String(255), nullable=True)
    agenda = Column(JSON, default=list, nullable=False)
    notes = Column(Text, nullable=True)
    audio_file_path = Column(Text, nullable=True)
    transcript_file_path = Column(Text, nullable=True)
    transcript_text = Column(Text, nullable=True)
    raw_transcription = Column(Text, nullable=True)
    cleaned_transcription = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    decisions = Column(JSON, default=list, nullable=False)
    action_items = Column(JSON, default=list, nullable=False)
    redacted_transcription = Column(Text, nullable=True)
    redacted_summary = Column(Text, nullable=True)
    redacted_decisions = Column(JSON, default=list, nullable=False)
    redacted_action_items = Column(JSON, default=list, nullable=False)
    email_draft = Column(Text, nullable=True)
    email_sent = Column(Boolean, default=False, nullable=False)
    email_response = Column(JSON, nullable=True)
    tokens_used = Column(Integer, default=0, nullable=False)
    credits_charged = Column(Boolean, default=False, nullable=False)
    status = Column(SQLEnum(MeetingStatus, native_enum=False), default=MeetingStatus.DRAFT, nullable=False, index=True)
    thread_id = Column(String(255), nullable=True, index=True)  # LangGraph checkpoint thread_id
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="meetings", foreign_keys=[user_id])
    team = relationship("Team", back_populates="meetings")
    project = relationship("Project", back_populates="meetings")
    creator = relationship(
        "User", back_populates="meetings_created", foreign_keys=[created_by]
    )
    attendees = relationship("Attendee", back_populates="meeting", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="meeting", cascade="all, delete-orphan")
    ai_override = relationship("MeetingAIOverride", back_populates="meeting", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_meetings_user_date", "user_id", "meeting_date"),
        Index("idx_meetings_user_status", "user_id", "status"),
        Index("idx_meetings_project", "project_name"),
        Index("idx_meetings_thread_id", "thread_id"),
    )

    def __repr__(self) -> str:
        return f"<Meeting(id={self.id}, title='{self.title}', status='{self.status.value}')>"


class Attendee(Base):
    """Meeting attendee model."""
    __tablename__ = "attendees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(PGUUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    meeting = relationship("Meeting", back_populates="attendees")

    __table_args__ = (
        Index("idx_attendees_meeting", "meeting_id"),
    )

    def __repr__(self) -> str:
        return f"<Attendee(meeting_id={self.meeting_id}, name='{self.name}', email='{self.email}')>"


class Task(Base):
    """Task model for PM tasks created from meetings."""
    __tablename__ = "tasks"

    id = Column(String(8), primary_key=True)
    meeting_id = Column(PGUUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    meeting_title = Column(String(500), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(TaskStatus, native_enum=False), default=TaskStatus.TODO, nullable=False, index=True)
    priority = Column(SQLEnum(TaskPriority, native_enum=False), default=TaskPriority.MEDIUM, nullable=False)
    assignee = Column(String(255), nullable=True)
    due_date = Column(Date, nullable=True)
    labels = Column(JSON, default=list, nullable=False)
    action_item_index = Column(Integer, nullable=False)
    github_issue_number = Column(Integer, nullable=True)
    github_issue_url = Column(Text, nullable=True)
    synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    meeting = relationship("Meeting", back_populates="tasks")
    team = relationship("Team", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    assigned_user = relationship(
        "User", back_populates="assigned_tasks", foreign_keys=[assigned_user_id]
    )

    __table_args__ = (
        Index("idx_tasks_meeting", "meeting_id"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_assignee", "assignee"),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}')>"
