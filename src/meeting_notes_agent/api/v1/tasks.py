"""Tasks API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional, List
from uuid import UUID

from meeting_notes_agent.auth.dependencies import get_current_user_id, get_current_user
from meeting_notes_agent.database.models import TaskStatus, TaskPriority
from meeting_notes_agent.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
)
from meeting_notes_agent.services import TaskService
from meeting_notes_agent.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Create a new task."""
    task_service = TaskService()
    try:
        return task_service.create_task(current_user_id, data)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    meeting_id: Optional[UUID] = None,
    task_status: Optional[TaskStatus] = Query(None, alias="status"),
):
    """List user's tasks."""
    task_service = TaskService()
    return task_service.list_tasks(
        user_id=current_user_id,
        page=page,
        page_size=page_size,
        meeting_id=meeting_id,
        status=task_status,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Get task by ID."""
    task_service = TaskService()
    try:
        return task_service.get_task(task_id, current_user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Update a task."""
    task_service = TaskService()
    try:
        return task_service.update_task(task_id, current_user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Delete a task."""
    task_service = TaskService()
    try:
        task_service.delete_task(task_id, current_user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def mark_task_complete(
    task_id: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Mark task as complete."""
    task_service = TaskService()
    try:
        return task_service.mark_task_complete(task_id, current_user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
