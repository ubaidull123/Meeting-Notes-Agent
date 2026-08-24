"""Settings API schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


UsageMode = Literal["app_credits", "byok"]


class ProfileSettingsResponse(BaseModel):
    display_name: str
    email: EmailStr
    timezone: str
    language: Literal["en", "ur"]
    date_format: Literal["yyyy-mm-dd", "dd-mm-yyyy", "mm-dd-yyyy"]
    time_format: Literal["12h", "24h"]
    organization: str | None = None
    job_title: str | None = None


class ProfileSettingsUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    timezone: str = Field(min_length=1, max_length=100)
    language: Literal["en", "ur"]
    date_format: Literal["yyyy-mm-dd", "dd-mm-yyyy", "mm-dd-yyyy"]
    time_format: Literal["12h", "24h"]
    organization: str | None = Field(default=None, max_length=255)
    job_title: str | None = Field(default=None, max_length=255)

    @field_validator("display_name", "timezone")
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be empty.")
        return value

    @field_validator("organization", "job_title")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        value = value.strip() if value else None
        return value or None


class CredentialPublic(BaseModel):
    provider: str
    has_api_key: bool
    api_key_hint: str | None = None
    is_valid: bool
    last_tested_at: datetime | None = None
    last_test_error: str | None = None
    configuration: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class AISettingsResponse(BaseModel):
    llm_usage_mode: UsageMode
    llm_provider: str
    llm_model: str | None
    transcription_usage_mode: UsageMode
    transcription_provider: str
    transcription_model: str | None
    temperature: float = 0.2
    max_output_tokens: int = 1200
    response_language: str = "auto"
    credentials: list[CredentialPublic] = Field(default_factory=list)


class AISettingsUpdate(BaseModel):
    llm_usage_mode: UsageMode
    llm_provider: str
    llm_model: str
    transcription_usage_mode: UsageMode
    transcription_provider: str
    transcription_model: str
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_output_tokens: int = Field(default=1200, ge=128, le=16000)
    response_language: str = Field(default="auto", min_length=2, max_length=50)


class TranscriptionSettingsResponse(BaseModel):
    usage_mode: UsageMode
    provider: str
    model: str
    language: str = "auto"
    credentials: list[CredentialPublic] = Field(default_factory=list)


class TranscriptionSettingsUpdate(BaseModel):
    usage_mode: UsageMode
    provider: str
    model: str
    language: str = Field(default="auto", min_length=2, max_length=20)


SummaryStyle = Literal["short", "standard", "detailed", "executive", "technical", "custom"]
SummarySection = Literal[
    "main_topics",
    "decisions",
    "risks",
    "questions",
    "action_items",
    "deadlines",
    "follow_up_recommendations",
]


class MeetingDefaultsResponse(BaseModel):
    default_meeting_type: Literal["general", "planning", "standup", "interview", "client"]
    generate_summary: bool
    generate_action_items: bool
    generate_decisions: bool
    generate_insights: bool
    generate_follow_up_email: bool
    require_human_review: bool
    require_email_approval: bool
    redact_sensitive_information: bool
    summary_style: SummaryStyle
    summary_sections: list[SummarySection]
    custom_instructions: str | None = None


class MeetingDefaultsUpdate(MeetingDefaultsResponse):
    custom_instructions: str | None = Field(default=None, max_length=4000)

    @field_validator("summary_sections")
    @classmethod
    def unique_summary_sections(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))

    @field_validator("custom_instructions")
    @classmethod
    def normalize_instructions(cls, value: str | None) -> str | None:
        value = value.strip() if value else None
        return value or None


class NotificationSettingsResponse(BaseModel):
    processing_finished: bool
    processing_failed: bool
    review_required: bool
    email_approval_required: bool
    credits_low: bool
    delivery_available: bool = False


class NotificationSettingsUpdate(BaseModel):
    processing_finished: bool
    processing_failed: bool
    review_required: bool
    email_approval_required: bool
    credits_low: bool


class PrivacySettingsResponse(BaseModel):
    recording_retention: Literal["never", "24_hours", "7_days", "30_days"]
    keep_transcript: bool
    automatic_cleanup_available: bool = False


class PrivacySettingsUpdate(BaseModel):
    recording_retention: Literal["never", "24_hours", "7_days", "30_days"]
    keep_transcript: bool


class UsageSummaryResponse(BaseModel):
    balance: int
    meetings_processed: int
    tokens_used: int
    credits_consumed: int
    llm_requests: int
    llm_credits: int
    transcription_requests: int
    transcription_credits: int


class CredentialSaveRequest(BaseModel):
    provider: str
    api_key: str = Field(..., min_length=1)
    config: dict[str, Any] | None = None


class CredentialTestRequest(BaseModel):
    provider: str
    api_key: str | None = None
    config: dict[str, Any] | None = None


class CredentialTestResponse(BaseModel):
    valid: bool
    provider: str
    message: str


class EmailSettingsResponse(BaseModel):
    email_mode: UsageMode
    provider: str
    sender_name: str | None = None
    sender_email: str | None = None
    reply_to_email: str | None = None
    sending_domain: str | None = None
    domain_status: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_use_tls: bool = True


class EmailSettingsUpdate(BaseModel):
    email_mode: UsageMode
    provider: str
    sender_name: str | None = None
    sender_email: EmailStr | None = None
    reply_to_email: EmailStr | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_use_tls: bool = True


class CreditBalanceResponse(BaseModel):
    balance: int


class CreditTransactionResponse(BaseModel):
    id: UUID
    meeting_id: UUID | None
    amount: int
    balance_after: int
    transaction_type: str
    service_type: str | None
    provider: str | None
    model: str | None
    usage_mode: str | None
    usage_metadata: dict[str, Any] | None
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsageRecordResponse(BaseModel):
    id: UUID
    meeting_id: UUID
    service_type: str
    provider: str
    model: str
    usage_mode: str
    input_tokens: int
    output_tokens: int
    audio_duration_seconds: int
    credits_cost: int
    status: str
    error_message: str | None
    created_at: datetime
    meeting_title: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MeetingOverrideRequest(BaseModel):
    llm_usage_mode: UsageMode | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    transcription_usage_mode: UsageMode | None = None
    transcription_provider: str | None = None
    transcription_model: str | None = None
    email_mode: UsageMode | None = None
    email_provider: str | None = None

class MeetingOverrideResponse(MeetingOverrideRequest):
    pass
