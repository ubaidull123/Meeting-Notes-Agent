"""Task models for GitHub PM tasks system."""
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import uuid


class TaskStatus(str, Enum):
    """Task status options."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(BaseModel):
    """Represents a task created from meeting action items."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(..., min_length=1, description="Task title")
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    labels: List[str] = Field(default_factory=list)
    meeting_id: str = Field(..., description="Source meeting ID")
    meeting_title: str = Field(..., description="Source meeting title")
    action_item_index: int = Field(..., description="Index in original action items list")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    github_issue_number: Optional[int] = None
    github_issue_url: Optional[str] = None
    synced_at: Optional[datetime] = None

    @field_validator('updated_at', mode='before')
    @classmethod
    def set_updated_at(cls, v):
        return datetime.now() if v is None else v

    def to_github_issue_body(self) -> str:
        """Generate GitHub issue body from task."""
        lines = [
            f"## Source Meeting",
            f"- **Meeting:** {self.meeting_title}",
            f"- **Meeting ID:** {self.meeting_id}",
            f"- **Action Item Index:** {self.action_item_index}",
            "",
            f"## Description",
            self.description or self.title,
        ]
        if self.due_date:
            lines.extend(["", f"**Due Date:** {self.due_date}"])
        if self.assignee:
            lines.extend(["", f"**Assignee:** {self.assignee}"])
        return "\n".join(lines)


class TaskCollection(BaseModel):
    """Collection of tasks for a meeting."""
    meeting_id: str
    meeting_title: str
    tasks: List[Task] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    synced_at: Optional[datetime] = None