"""User-facing product preferences and profile settings."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from meeting_notes_agent.config.core.exceptions import NotFoundError
from meeting_notes_agent.database.models import User
from meeting_notes_agent.database.models_ai_config import UserProductSettings


DEFAULT_PRODUCT_SETTINGS: dict[str, Any] = {
    "timezone": "UTC",
    "language": "en",
    "date_format": "yyyy-mm-dd",
    "time_format": "12h",
    "organization": None,
    "job_title": None,
    "ai_temperature": 0.2,
    "ai_max_output_tokens": 1200,
    "response_language": "auto",
    "transcription_language": "auto",
    "default_meeting_type": "general",
    "generate_summary": True,
    "generate_action_items": True,
    "generate_decisions": True,
    "generate_insights": True,
    "generate_follow_up_email": True,
    "require_human_review": True,
    "require_email_approval": True,
    "redact_sensitive_information": True,
    "summary_style": "standard",
    "summary_sections": ["main_topics", "decisions", "action_items", "deadlines"],
    "custom_instructions": None,
    "notify_processing_finished": True,
    "notify_processing_failed": True,
    "notify_review_required": True,
    "notify_email_approval_required": True,
    "notify_credits_low": True,
    "recording_retention": "never",
    "keep_transcript": True,
}


class ProductSettingsService:
    """Own the non-provider product settings for one authenticated user."""

    def __init__(self, db: Session):
        self.db = db

    def get_product_settings(self, user_id: int, *, create: bool = False) -> UserProductSettings:
        settings = self.db.query(UserProductSettings).filter_by(user_id=user_id).first()
        if settings is None:
            settings = UserProductSettings(user_id=user_id, **DEFAULT_PRODUCT_SETTINGS)
            if create:
                self.db.add(settings)
                self.db.flush()
        return settings

    def get_profile(self, user_id: int) -> dict[str, Any]:
        user = self.db.query(User).filter_by(id=user_id).first()
        if user is None:
            raise NotFoundError("User not found")
        settings = self.get_product_settings(user_id)
        return {
            "display_name": user.full_name,
            "email": user.email,
            "timezone": settings.timezone,
            "language": settings.language,
            "date_format": settings.date_format,
            "time_format": settings.time_format,
            "organization": settings.organization,
            "job_title": settings.job_title,
        }

    def update_profile(self, user_id: int, **values: Any) -> dict[str, Any]:
        user = self.db.query(User).filter_by(id=user_id).first()
        if user is None:
            raise NotFoundError("User not found")
        settings = self.get_product_settings(user_id, create=True)
        user.full_name = values.pop("display_name")
        for key, value in values.items():
            setattr(settings, key, value)
        settings.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return self.get_profile(user_id)

    def get_ai_advanced(self, user_id: int) -> dict[str, Any]:
        settings = self.get_product_settings(user_id)
        return {
            "temperature": settings.ai_temperature,
            "max_output_tokens": settings.ai_max_output_tokens,
            "response_language": settings.response_language,
        }

    def update_ai_advanced(
        self,
        user_id: int,
        *,
        temperature: float,
        max_output_tokens: int,
        response_language: str,
    ) -> None:
        settings = self.get_product_settings(user_id, create=True)
        settings.ai_temperature = temperature
        settings.ai_max_output_tokens = max_output_tokens
        settings.response_language = response_language.strip()
        settings.updated_at = datetime.now(timezone.utc)
        self.db.flush()

    def get_transcription_preferences(self, user_id: int) -> dict[str, Any]:
        settings = self.get_product_settings(user_id)
        return {"language": settings.transcription_language}

    def update_transcription_preferences(self, user_id: int, *, language: str) -> None:
        settings = self.get_product_settings(user_id, create=True)
        settings.transcription_language = language.strip().lower()
        settings.updated_at = datetime.now(timezone.utc)
        self.db.flush()

    def get_meeting_defaults(self, user_id: int) -> dict[str, Any]:
        settings = self.get_product_settings(user_id)
        keys = (
            "default_meeting_type",
            "generate_summary",
            "generate_action_items",
            "generate_decisions",
            "generate_insights",
            "generate_follow_up_email",
            "require_human_review",
            "require_email_approval",
            "redact_sensitive_information",
            "summary_style",
            "summary_sections",
            "custom_instructions",
        )
        return {key: getattr(settings, key) for key in keys}

    def update_meeting_defaults(self, user_id: int, **values: Any) -> dict[str, Any]:
        settings = self.get_product_settings(user_id, create=True)
        for key, value in values.items():
            setattr(settings, key, value)
        settings.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return self.get_meeting_defaults(user_id)

    def get_notifications(self, user_id: int) -> dict[str, Any]:
        settings = self.get_product_settings(user_id)
        return {
            "processing_finished": settings.notify_processing_finished,
            "processing_failed": settings.notify_processing_failed,
            "review_required": settings.notify_review_required,
            "email_approval_required": settings.notify_email_approval_required,
            "credits_low": settings.notify_credits_low,
            "delivery_available": False,
        }

    def update_notifications(self, user_id: int, **values: bool) -> dict[str, Any]:
        settings = self.get_product_settings(user_id, create=True)
        for key, value in values.items():
            setattr(settings, f"notify_{key}", value)
        settings.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return self.get_notifications(user_id)

    def get_privacy(self, user_id: int) -> dict[str, Any]:
        settings = self.get_product_settings(user_id)
        return {
            "recording_retention": settings.recording_retention,
            "keep_transcript": settings.keep_transcript,
            "automatic_cleanup_available": False,
        }

    def update_privacy(self, user_id: int, **values: Any) -> dict[str, Any]:
        settings = self.get_product_settings(user_id, create=True)
        settings.recording_retention = values["recording_retention"]
        settings.keep_transcript = values["keep_transcript"]
        settings.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return self.get_privacy(user_id)
