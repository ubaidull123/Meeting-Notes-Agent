"""
Single universal state schema for the meeting notes agent.
Combines input fields and all pipeline outputs into one Pydantic model.
"""
from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
import uuid
from meeting_notes_agent.models.task import Task, TaskCollection


class Attendee(BaseModel):
    """Represents a meeting attendee with name and email."""
    name: str = Field(..., min_length=1, description="Full name of the attendee")
    email: str = Field(..., min_length=3, description="Email address of the attendee")


class ResolvedAIConfiguration(BaseModel):
    usage_mode: str = "app_credits"
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_output_tokens: int = 1200
    response_language: str = "auto"


class ResolvedTranscriptionConfiguration(BaseModel):
    usage_mode: str = "app_credits"
    provider: str = "openai"
    model: str = "gpt-4o-mini-transcribe"
    language: str = "auto"


class ResolvedMeetingConfiguration(BaseModel):
    ai: ResolvedAIConfiguration = Field(default_factory=ResolvedAIConfiguration)
    transcription: ResolvedTranscriptionConfiguration = Field(default_factory=ResolvedTranscriptionConfiguration)
    email_mode: str = "app_credits"
    email_provider: str = "resend"
    default_meeting_type: str = "general"
    generate_summary: bool = True
    generate_action_items: bool = True
    generate_decisions: bool = True
    generate_insights: bool = True
    generate_follow_up_email: bool = True
    require_human_review: bool = True
    require_email_approval: bool = True
    redact_sensitive_information: bool = True
    summary_style: str = "standard"
    summary_sections: List[str] = Field(default_factory=lambda: ["main_topics", "decisions", "action_items", "deadlines"])
    custom_instructions: Optional[str] = None


class MeetingState(BaseModel):
    """
    Universal state for the meeting notes pipeline.
    All fields have defaults so LangGraph nodes can return partial updates.
    """
    # Identification & metadata
    meeting_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[int] = None
    meeting_title: str = Field(default="", min_length=0)
    meeting_date: date = Field(default_factory=lambda: date.today())
    meeting_time: Optional[str] = None
    project_name: Optional[str] = None
    configuration: Optional[ResolvedMeetingConfiguration] = None

    # Input sources (at least one must be provided initially)
    audio_file_path: Optional[str] = None
    transcript_file_path: Optional[str] = None
    transcript_text: Optional[str] = None

    # Attendees & agenda
    attendees: List[Attendee] = Field(default_factory=list)
    agenda: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

    # Pipeline outputs
    raw_transcription: Optional[str] = None
    cleaned_transcription: Optional[str] = None
    summary: Optional[str] = None
    decisions: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)

    # Redacted outputs (PII/confidential info removed)
    redacted_transcription: Optional[str] = None
    redacted_summary: Optional[str] = None
    redacted_decisions: List[str] = Field(default_factory=list)
    redacted_action_items: List[str] = Field(default_factory=list)
    email_draft: Optional[str] = None

    # Email outputs
    email_sent: bool = False
    email_response: Optional[dict] = None

    # PM Tasks outputs
    pm_tasks: List[Task] = Field(default_factory=list)
    task_collection: Optional[TaskCollection] = None

    # Storage outputs
    stored: bool = False
    storage_error: Optional[str] = None

    # Human review outputs
    human_review_decision: Optional[str] = None
    human_review_instructions: Optional[str] = None

    # Email review outputs (second review after draft)
    email_review_decision: Optional[str] = None
    email_review_instructions: Optional[str] = None

    # Token tracking
    tokens_used_accrued: int = 0

    @model_validator(mode="after")
    def validate_input_source(self) -> "MeetingState":
        """Reject conflicting sources while allowing LangGraph partial states."""
        has_audio = bool(self.audio_file_path)
        has_transcript_file = bool(self.transcript_file_path)
        has_transcript_text = bool(self.transcript_text)
        source_count = sum((has_audio, has_transcript_file, has_transcript_text))
        if source_count > 1:
            raise ValueError(
                "Provide only one of: audio_file_path, transcript_file_path, or transcript_text"
            )
        return self

    def to_input_dict(self) -> dict:
        """Extract only the input fields for backward compatibility."""
        return {
            "meeting_title": self.meeting_title,
            "meeting_date": self.meeting_date,
            "audio_file_path": self.audio_file_path,
            "transcript_file_path": self.transcript_file_path,
            "transcript_text": self.transcript_text,
            "attendees": self.attendees,
            "project_name": self.project_name,
            "meeting_time": self.meeting_time,
            "agenda": self.agenda,
            "notes": self.notes,
        }


# Audio format constants (moved from audio.py for single source of truth)
AUDIO_EXTENSIONS: frozenset[str] = frozenset({".mp3", ".wav", ".m4a"})
TRANSCRIPT_EXTENSIONS: frozenset[str] = frozenset({".txt", ".md", ".text", ".transcript"})


def validate_audio_path(path: str) -> str:
    """Validate audio file extension."""
    from pathlib import Path
    if Path(path).suffix.lower() not in AUDIO_EXTENSIONS:
        raise ValueError("Unsupported audio format. Supported formats: MP3, WAV, M4A")
    return path


def validate_transcript_path(path: str) -> str:
    """Validate transcript file extension."""
    from pathlib import Path
    if Path(path).suffix.lower() not in TRANSCRIPT_EXTENSIONS:
        raise ValueError("Unsupported transcript format. Use TXT, MD, or a text transcript file.")
    return path


# Backward-compat re-exports
AudioFormat = type("AudioFormat", (), {ext[1:].upper(): ext for ext in AUDIO_EXTENSIONS})
