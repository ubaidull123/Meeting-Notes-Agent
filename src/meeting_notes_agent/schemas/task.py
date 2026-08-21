"""Task schemas."""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from meeting_notes_agent.database.models import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """Task base schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = Field(default=None, max_length=255)
    due_date: Optional[date] = None
    labels: List[str] = Field(default_factory=list)


class TaskCreate(TaskBase):
    """Task creation schema."""
    meeting_id: UUID
    meeting_title: str
    action_item_index: int = Field(..., ge=0)


class TaskUpdate(BaseModel):
    """Task update schema."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = Field(default=None, max_length=255)
    due_date: Optional[date] = None
    labels: Optional[List[str]] = None


class TaskResponse(TaskBase):
    """Task response schema."""
    id: str
    meeting_id: UUID
    meeting_title: str
    action_item_index: int
    github_issue_number: Optional[int]
    github_issue_url: Optional[str]
    synced_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4",
                "title": "Prepare launch checklist",
                "description": "Create comprehensive checklist for October launch",
                "status": "todo",
                "priority": "high",
                "assignee": "John Doe",
                "due_date": "2024-09-30",
                "labels": ["meeting-action-item", "launch"],
                "meeting_id": "123e4567-e89b-12d3-a456-426614174000",
                "meeting_title": "Launch Planning",
                "action_item_index": 0,
                "github_issue_number": None,
                "github_issue_url": None,
                "synced_at": None,
                "created_at": "2024-08-20T10:30:00Z",
                "updated_at": "2024-08-20T10:30:00Z",
            }
        }
    )


class TaskListResponse(BaseModel):
    """Task list response with pagination."""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int
