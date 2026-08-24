"""Meeting-level provider/model override service."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from meeting_notes_agent.config.core.exceptions import NotFoundError
from meeting_notes_agent.database.models import Meeting
from meeting_notes_agent.database.models_ai_config import AIUsageMode, MeetingAIOverride, ProviderType


class MeetingOverrideService:
    def __init__(self, db: Session):
        self.db = db

    def get_override(self, meeting_id: UUID, user_id: int) -> MeetingAIOverride | None:
        return self.db.query(MeetingAIOverride).filter_by(meeting_id=meeting_id, user_id=user_id).first()

    def set_override(self, meeting_id: UUID, user_id: int, **kwargs) -> MeetingAIOverride:
        meeting = self.db.query(Meeting).filter_by(id=meeting_id, user_id=user_id).first()
        if not meeting:
            raise NotFoundError("Meeting not found")
        override = self.get_override(meeting_id, user_id) or MeetingAIOverride(meeting_id=meeting_id, user_id=user_id)
        for key, value in kwargs.items():
            if value is None:
                setattr(override, key, None)
            elif key.endswith("usage_mode") or key == "email_mode":
                setattr(override, key, AIUsageMode(value))
            elif key.endswith("provider"):
                setattr(override, key, ProviderType(value))
            elif hasattr(override, key):
                setattr(override, key, value)
        self.db.add(override)
        self.db.flush()
        return override

    def clear_override(self, meeting_id: UUID, user_id: int) -> bool:
        override = self.get_override(meeting_id, user_id)
        if not override:
            return False
        self.db.delete(override)
        self.db.flush()
        return True

    def to_dict(self, meeting_id: UUID, user_id: int) -> dict | None:
        override = self.get_override(meeting_id, user_id)
        if not override:
            return None
        return {
            "llm_usage_mode": override.llm_usage_mode.value if override.llm_usage_mode else None,
            "llm_provider": override.llm_provider.value if override.llm_provider else None,
            "llm_model": override.llm_model,
            "transcription_usage_mode": override.transcription_usage_mode.value if override.transcription_usage_mode else None,
            "transcription_provider": override.transcription_provider.value if override.transcription_provider else None,
            "transcription_model": override.transcription_model,
            "email_mode": override.email_mode.value if override.email_mode else None,
            "email_provider": override.email_provider.value if override.email_provider else None,
        }

