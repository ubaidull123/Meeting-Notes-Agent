"""Central resolution of user, meeting override, and application defaults."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from meeting_notes_agent.services.ai_settings_service import AISettingsService
from meeting_notes_agent.services.email_settings_service import EmailSettingsService
from meeting_notes_agent.services.meeting_override_service import MeetingOverrideService
from meeting_notes_agent.services.product_settings_service import ProductSettingsService
from meeting_notes_agent.state_schema import (
    ResolvedAIConfiguration,
    ResolvedMeetingConfiguration,
    ResolvedTranscriptionConfiguration,
)


class UserConfigurationResolver:
    """Build a checkpoint-safe configuration without embedding credentials."""

    def __init__(self, db: Session):
        self.db = db

    def resolve(self, user_id: int, meeting_id: UUID | None = None) -> ResolvedMeetingConfiguration:
        override = MeetingOverrideService(self.db).to_dict(meeting_id, user_id) if meeting_id else None
        override = override or {}
        ai = AISettingsService(self.db).get_ai_config(user_id)
        product = ProductSettingsService(self.db)
        advanced = product.get_ai_advanced(user_id)
        transcription = product.get_transcription_preferences(user_id)
        meeting = product.get_meeting_defaults(user_id)
        email = EmailSettingsService(self.db).get_email_config(user_id)

        return ResolvedMeetingConfiguration(
            ai=ResolvedAIConfiguration(
                usage_mode=override.get("llm_usage_mode") or ai.llm_usage_mode.value,
                provider=override.get("llm_provider") or ai.llm_provider.value,
                model=override.get("llm_model") or ai.llm_model,
                **advanced,
            ),
            transcription=ResolvedTranscriptionConfiguration(
                usage_mode=override.get("transcription_usage_mode") or ai.transcription_usage_mode.value,
                provider=override.get("transcription_provider") or ai.transcription_provider.value,
                model=override.get("transcription_model") or ai.transcription_model,
                language=transcription["language"],
            ),
            email_mode=override.get("email_mode") or email.email_mode.value,
            email_provider=override.get("email_provider") or email.provider.value,
            **meeting,
        )
