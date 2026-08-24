"""Per-user email configuration service."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from meeting_notes_agent.config.core.exceptions import ValidationError
from meeting_notes_agent.database.models_ai_config import AIUsageMode, ProviderType, UserEmailConfig
from meeting_notes_agent.services.ai_settings_service import AISettingsService


class EmailSettingsService:
    def __init__(self, db: Session):
        self.db = db

    def get_email_config(self, user_id: int) -> UserEmailConfig:
        config = self.db.query(UserEmailConfig).filter_by(user_id=user_id).first()
        if not config:
            config = UserEmailConfig(user_id=user_id, email_mode=AIUsageMode.APP_CREDITS, provider=ProviderType.RESEND)
            self.db.add(config)
            self.db.flush()
        return config

    def update_email_config(self, user_id: int, **kwargs) -> UserEmailConfig:
        provider = kwargs.get("provider", "resend")
        if provider not in {"resend", "mailgun"}:
            raise ValidationError("Email provider is not supported.", code="EMAIL_CONFIGURATION_INVALID")
        sender_email = kwargs.get("sender_email")
        if sender_email and "@" not in sender_email:
            raise ValidationError("Sender email must be valid.", code="EMAIL_CONFIGURATION_INVALID")
        config = self.get_email_config(user_id)
        for key, value in kwargs.items():
            if hasattr(config, key) and key not in {"user_id", "credential_id"}:
                if key == "email_mode":
                    value = AIUsageMode(value)
                elif key == "provider":
                    value = ProviderType(value)
                setattr(config, key, value)
        config.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return config

    def resolve_sender(self, user_id: int) -> str | None:
        config = self.get_email_config(user_id)
        if config.sender_email and config.sender_name:
            return f"{config.sender_name} <{config.sender_email}>"
        return config.sender_email

    def resolve_delivery_config(self, user_id: int) -> dict:
        config = self.get_email_config(user_id)
        provider = config.provider.value if hasattr(config.provider, "value") else str(config.provider)
        api_key = None
        provider_config = {}
        if config.email_mode == AIUsageMode.BYOK:
            credential_service = AISettingsService(self.db)
            api_key = credential_service.get_decrypted_credential(user_id, provider)
            if not api_key:
                raise ValidationError(f"Your {provider.title()} API key is missing.", code="EMAIL_CONFIGURATION_INVALID")
            provider_config = credential_service.get_credential_config(user_id, provider)
            if provider == ProviderType.MAILGUN.value and not provider_config.get("domain"):
                raise ValidationError("Your Mailgun domain is missing.", code="EMAIL_CONFIGURATION_INVALID")
        return {
            "mode": config.email_mode.value if hasattr(config.email_mode, "value") else str(config.email_mode),
            "provider": provider,
            "from_email": self.resolve_sender(user_id),
            "api_key": api_key,
            "provider_config": provider_config,
            "reply_to": config.reply_to_email,
        }
