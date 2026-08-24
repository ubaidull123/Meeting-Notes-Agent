"""Meetings API routes."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query, File, UploadFile, Form
from typing import Annotated, Optional, List
from uuid import UUID

from meeting_notes_agent.auth.dependencies import get_current_user_id, get_current_user, require_admin
from meeting_notes_agent.database.models import MeetingStatus
from meeting_notes_agent.schemas.meeting import (
    AttendeeBase,
    MeetingCreate,
    MeetingUpdate,
    MeetingListItem,
    MeetingResponse,
    MeetingStatusResponse,
    MeetingResultResponse,
    AudioUploadResponse,
    TranscriptUploadResponse,
    ProcessingStartResponse,
    ReviewContentResponse,
    ReviewRequest,
    ReviewResponse,
    EmailDraftResponse,
    EmailReviewRequest,
    EmailSendResponse,
)
from meeting_notes_agent.services import ProcessingService
from meeting_notes_agent.services.processing_service import process_meeting_in_background
from meeting_notes_agent.config.core.exceptions import (
    InsufficientCreditsError,
    NotFoundError,
    ProcessingError,
    QuotaExceededError,
    ValidationError,
    to_http_exception,
)
from meeting_notes_agent.config.core.config import settings

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    data: MeetingCreate,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Create a new meeting."""
    processing_service = ProcessingService()
    try:
        meeting = processing_service.create_meeting(current_user_id, data)
        return MeetingResponse.model_validate(meeting)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[MeetingListItem])
async def list_meetings(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    meeting_status: Optional[MeetingStatus] = Query(None, alias="status"),
):
    """List user's meetings."""
    processing_service = ProcessingService()
    meetings, total = processing_service.list_meetings(
        user_id=current_user_id,
        page=page,
        page_size=page_size,
        status=meeting_status,
    )
    return [MeetingListItem.model_validate(m) for m in meetings]


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Get meeting by ID."""
    processing_service = ProcessingService()
    try:
        meeting = processing_service.get_meeting(meeting_id, current_user_id)
        return MeetingResponse.model_validate(meeting)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    data: MeetingUpdate,
):
    """Update meeting metadata."""
    processing_service = ProcessingService()
    try:
        meeting = processing_service.update_meeting(meeting_id, current_user_id, data)
        return MeetingResponse.model_validate(meeting)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Delete a meeting."""
    processing_service = ProcessingService()
    try:
        processing_service.delete_meeting(meeting_id, current_user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{meeting_id}/audio", response_model=AudioUploadResponse)
async def upload_audio(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    file: Annotated[UploadFile, File(...)],
):
    """Upload audio file for meeting."""
    # Validate file type
    from pathlib import Path
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".mp3", ".wav", ".m4a"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio format. Supported formats: MP3, WAV, M4A"
        )

    # Check file size
    max_size = settings.max_upload_size_mb * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
        )

    # Save file
    import os
    import uuid
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{uuid.uuid4()}{suffix}")
    with open(file_path, "wb") as f:
        f.write(content)

    processing_service = ProcessingService()
    try:
        return processing_service.upload_audio(meeting_id, current_user_id, file_path, len(content))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{meeting_id}/transcript", response_model=TranscriptUploadResponse)
async def upload_transcript(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    file: Annotated[UploadFile, File(...)],
):
    """Upload transcript file for meeting."""
    # Validate file type
    from pathlib import Path
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".txt", ".md", ".text", ".transcript"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported transcript format. Use TXT, MD, or a text transcript file."
        )

    # Save file
    import os
    import uuid
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{uuid.uuid4()}{suffix}")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    processing_service = ProcessingService()
    try:
        return processing_service.upload_transcript(meeting_id, current_user_id, file_path)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{meeting_id}/process", response_model=ProcessingStartResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_processing(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
    background_tasks: BackgroundTasks,
):
    """Queue meeting processing and return immediately."""
    processing_service = ProcessingService()
    try:
        queued = processing_service.queue_processing(meeting_id, current_user_id)
        background_tasks.add_task(
            process_meeting_in_background,
            meeting_id,
            current_user_id,
            queued.thread_id,
        )
        return queued
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (QuotaExceededError, InsufficientCreditsError) as e:
        raise to_http_exception(e)
    except ProcessingError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{meeting_id}/cancel", response_model=MeetingStatusResponse)
async def cancel_processing(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Stop an active or paused meeting workflow."""
    processing_service = ProcessingService()
    try:
        return processing_service.cancel_processing(meeting_id, current_user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{meeting_id}/status", response_model=MeetingStatusResponse)
async def get_meeting_status(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Get meeting processing status."""
    processing_service = ProcessingService()
    try:
        return processing_service.get_meeting_status(meeting_id, current_user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Human Review Checkpoints
@router.get("/{meeting_id}/review", response_model=ReviewContentResponse)
async def get_review_content(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Get content for human review."""
    processing_service = ProcessingService()
    try:
        return processing_service.get_review_content(meeting_id, current_user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{meeting_id}/review", response_model=ReviewResponse)
async def submit_review(
    meeting_id: UUID,
    data: ReviewRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Submit human review decision."""
    processing_service = ProcessingService()
    try:
        return processing_service.resume_processing(meeting_id, current_user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ProcessingError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Email Review Checkpoint
@router.get("/{meeting_id}/email-review", response_model=EmailDraftResponse)
async def get_email_draft(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Get email draft for review."""
    processing_service = ProcessingService()
    try:
        return processing_service.get_email_draft(meeting_id, current_user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{meeting_id}/email-review", response_model=EmailSendResponse)
async def submit_email_review(
    meeting_id: UUID,
    data: EmailReviewRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Submit email review decision."""
    processing_service = ProcessingService()
    try:
        return processing_service.review_email(meeting_id, current_user_id, data)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ProcessingError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Results
@router.get("/{meeting_id}/results", response_model=MeetingResultResponse)
async def get_meeting_results(
    meeting_id: UUID,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """Get meeting results."""
    processing_service = ProcessingService()
    try:
        return processing_service.get_meeting_results(meeting_id, current_user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
