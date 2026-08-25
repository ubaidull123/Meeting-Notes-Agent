"""Meeting schemas."""
from datetime import date, datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID


class AttendeeBase(BaseModel):
    """Attendee base schema."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    user_id: Optional[int] = None
    title: Optional[str] = Field(default=None, max_length=255)
    department: Optional[str] = Field(default=None, max_length=255)


class AttendeeResponse(AttendeeBase):
    """Attendee response schema."""
    id: int
    meeting_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingBase(BaseModel):
    """Meeting base schema."""
    title: str = Field(..., min_length=1, max_length=500, description="Meeting title")
    meeting_date: date = Field(default_factory=date.today, description="Meeting date")
    meeting_time: Optional[str] = Field(default=None, max_length=50, description="Meeting time")
    project_name: Optional[str] = Field(default=None, max_length=255, description="Project name")
    agenda: List[str] = Field(default_factory=list, description="Agenda items")
    notes: Optional[str] = Field(default=None, description="Additional notes")
    attendees: List[AttendeeBase] = Field(default_factory=list, description="Legacy/free-text meeting attendees")


class MeetingCreate(MeetingBase):
    """Meeting creation schema."""
    # Exactly one of these should be provided
    audio_file_path: Optional[str] = None
    transcript_file_path: Optional[str] = None
    transcript_text: Optional[str] = None
    team_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    participant_user_ids: Optional[List[int]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Q3 Planning Meeting",
                "meeting_date": "2024-08-20",
                "meeting_time": "10:00",
                "project_name": "Product Planning",
                "agenda": ["Review Q2", "Plan Q3", "Budget allocation"],
                "notes": "Quarterly planning session",
                "attendees": [
                    {"name": "John Doe", "email": "john@company.com"},
                    {"name": "Jane Smith", "email": "jane@company.com"}
                ],
                "transcript_text": "Speaker 1: Good morning everyone..."
            }
        }
    )


class MeetingUpdate(BaseModel):
    """Meeting update schema with draft-only source replacement."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    meeting_date: Optional[date] = None
    meeting_time: Optional[str] = Field(default=None, max_length=50)
    project_name: Optional[str] = Field(default=None, max_length=255)
    project_id: Optional[UUID] = None
    agenda: Optional[List[str]] = None
    notes: Optional[str] = None
    attendees: Optional[List[AttendeeBase]] = None
    participant_user_ids: Optional[List[int]] = None
    transcript_text: Optional[str] = None


class MeetingListItem(BaseModel):
    """Meeting list item schema."""
    id: UUID
    title: str
    meeting_date: date
    meeting_time: Optional[str]
    project_name: Optional[str]
    team_id: UUID
    project_id: Optional[UUID]
    created_by: int
    created_by_name: Optional[str] = None
    participant_count: int = 0
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingResponse(MeetingBase):
    """Meeting response schema."""
    id: UUID
    user_id: int
    team_id: UUID
    project_id: Optional[UUID]
    created_by: int
    created_by_name: Optional[str] = None
    status: str
    audio_file_path: Optional[str]
    transcript_file_path: Optional[str]
    transcript_text: Optional[str]
    raw_transcription: Optional[str]
    cleaned_transcription: Optional[str]
    summary: Optional[str]
    decisions: List[str]
    action_items: List[str]
    redacted_transcription: Optional[str]
    redacted_summary: Optional[str]
    redacted_decisions: List[str]
    redacted_action_items: List[str]
    email_draft: Optional[str]
    email_sent: bool
    email_response: Optional[dict]
    restrict_to_participants: bool
    tokens_used: int
    thread_id: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    attendees: List[AttendeeResponse]

    model_config = ConfigDict(from_attributes=True)


class MeetingStatusResponse(BaseModel):
    """Meeting processing status response."""
    meeting_id: UUID
    status: str
    current_stage: Optional[str] = None
    error: Optional[str] = None
    progress_percentage: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "meeting_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "processing",
                "current_stage": "summarization",
                "error": None,
                "progress_percentage": 60
            }
        }
    )


class MeetingResultResponse(BaseModel):
    """Meeting results response (for frontend consumption)."""
    meeting_id: UUID
    title: str
    meeting_date: date
    summary: Optional[str]
    decisions: List[str]
    action_items: List[str]
    redacted_summary: Optional[str]
    redacted_decisions: List[str]
    redacted_action_items: List[str]
    email_draft: Optional[str]
    email_sent: bool
    tasks: List["TaskResponse"]
    status: str
    tokens_used: int

    model_config = ConfigDict(from_attributes=True)


class AudioUploadResponse(BaseModel):
    """Audio upload response."""
    meeting_id: UUID
    file_path: str
    file_size: int
    status: str


class TranscriptUploadResponse(BaseModel):
    """Transcript upload response."""
    meeting_id: UUID
    file_path: str
    status: str


class ProcessingStartResponse(BaseModel):
    """Processing start response."""
    meeting_id: UUID
    thread_id: str
    status: str
    message: str


# Human Review Schemas
class ReviewContentResponse(BaseModel):
    """Review content response."""
    meeting_id: UUID
    meeting_title: str
    redacted_transcription: str
    redacted_summary: str
    redacted_decisions: List[str]
    redacted_action_items: List[str]

    model_config = ConfigDict(from_attributes=True)


class ReviewRequest(BaseModel):
    """Review request schema."""
    decision: Literal["approve", "reject", "revise"] = Field(..., description="Review decision")
    instructions: Optional[str] = Field(default=None, description="Revision instructions (required for revise)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decision": "approve",
                "instructions": None
            }
        }
    )


class ReviewResponse(BaseModel):
    """Review response schema."""
    meeting_id: UUID
    decision: str
    message: str
    next_status: str


# Email Review Schemas
class EmailDraftResponse(BaseModel):
    """Email draft response."""
    meeting_id: UUID
    meeting_title: str
    email_draft: str
    redacted_summary: str
    redacted_decisions: List[str]
    redacted_action_items: List[str]
    participants: List["EmailParticipantResponse"] = Field(default_factory=list)
    delivery_error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EmailReviewRequest(BaseModel):
    """Email review request schema."""
    decision: Literal["approve", "reject", "revise"] = Field(..., description="Email review decision")
    instructions: Optional[str] = Field(default=None, description="Revision instructions (required for revise)")
    recipient_user_ids: Optional[List[int]] = Field(
        default=None,
        description="Meeting participant user IDs selected for this meeting's follow-up",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "decision": "approve",
                "instructions": None
            }
        }
    )


class EmailSendResponse(BaseModel):
    """Email send response."""
    meeting_id: UUID
    sent: bool
    response: Optional[dict]
    message: str


class EmailParticipantResponse(BaseModel):
    user_id: int
    name: str
    email: str
    title: Optional[str] = None
    department: Optional[str] = None
    selected: bool = False
    delivery_status: Optional[str] = None


# Task schemas (will be defined in task.py but imported here)
class TaskResponse(BaseModel):
    """Task response schema (placeholder for forward reference)."""
    id: str
    title: str
    description: Optional[str]
    status: str
    priority: str
    assignee: Optional[str]
    due_date: Optional[date]
    labels: List[str]
    meeting_id: UUID
    meeting_title: str
    action_item_index: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Forward references
MeetingResultResponse.model_rebuild()
EmailDraftResponse.model_rebuild()
