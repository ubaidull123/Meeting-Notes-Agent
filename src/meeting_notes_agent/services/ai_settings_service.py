"""Per-user AI settings, credentials, and resolution service."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from openai import OpenAI
from sqlalchemy.orm import Session

from meeting_notes_agent.config.providers import (
    get_available_models,
    provider_enabled,
    provider_supports,
    validate_model,
)
from meeting_notes_agent.config.core.config import Settings
from meeting_notes_agent.config.core.exceptions import InsufficientCreditsError, ValidationError
from meeting_notes_agent.database.models import UserCredits
from meeting_notes_agent.database.models_ai_config import AIUsageMode, ProviderType, UserAIConfig, UserCredential
from meeting_notes_agent.services.credential_encryption import CredentialEncryptionService


class AISettingsService:
    """Manage AI defaults, encrypted BYOK credentials, and runtime resolution."""

    def __init__(self, db: Session):
        self.db = db
        self.encryption = CredentialEncryptionService()

    def get_ai_config(self, user_id: int) -> UserAIConfig:
        config = self.db.query(UserAIConfig).filter_by(user_id=user_id).first()
        if not config:
            settings = Settings()
            config = UserAIConfig(
                user_id=user_id,
                llm_usage_mode=AIUsageMode.APP_CREDITS,
                llm_provider=ProviderType.OPENAI,
                llm_model=getattr(settings, "openai_chat_model", None) or "gpt-4o-mini",
                transcription_usage_mode=AIUsageMode.APP_CREDITS,
                transcription_provider=ProviderType.OPENAI,
                transcription_model=getattr(settings, "openai_transcription_model", None) or "gpt-4o-mini-transcribe",
            )
            self.db.add(config)
            self.db.flush()
        return config

    def list_credentials(self, user_id: int) -> list[UserCredential]:
        return self.db.query(UserCredential).filter_by(user_id=user_id).all()

    def get_credential(self, user_id: int, provider: str) -> UserCredential | None:
        return self.db.query(UserCredential).filter_by(user_id=user_id, provider=ProviderType(provider)).first()

    def save_credential(self, user_id: int, provider: str, api_key: str, config: dict[str, Any] | None = None) -> UserCredential:
        provider_type = ProviderType(provider)
        credential = self.get_credential(user_id, provider) or UserCredential(user_id=user_id, provider=provider_type)
        credential.api_key_encrypted = self.encryption.encrypt(api_key)
        credential.api_key_hint = CredentialEncryptionService.mask_key(api_key)
        credential.config_encrypted = self.encryption.encrypt_json(config or {})
        credential.is_valid = False
        credential.last_tested_at = None
        credential.last_test_error = None
        if credential.id is None:
            self.db.add(credential)
        self.db.flush()
        return credential

    def delete_credential(self, user_id: int, provider: str) -> bool:
        credential = self.get_credential(user_id, provider)
        if not credential:
            return False
        self.db.delete(credential)
        self.db.flush()
        return True

    def get_decrypted_credential(self, user_id: int, provider: str) -> str | None:
        credential = self.get_credential(user_id, provider)
        if not credential or not credential.api_key_encrypted:
            return None
        return self.encryption.decrypt(credential.api_key_encrypted)

    def get_credential_config(self, user_id: int, provider: str) -> dict[str, Any]:
        credential = self.get_credential(user_id, provider)
        return self.encryption.decrypt_json(credential.config_encrypted) if credential else {}

    def get_public_credential_config(self, credential: UserCredential) -> dict[str, str]:
        config = self.encryption.decrypt_json(credential.config_encrypted)
        return {
            key: str(value)
            for key, value in config.items()
            if key in {"domain"} and value
        }

    def update_ai_config(
        self,
        user_id: int,
        *,
        llm_usage_mode: str,
        llm_provider: str,
        llm_model: str,
        transcription_usage_mode: str,
        transcription_provider: str,
        transcription_model: str,
    ) -> UserAIConfig:
        self._validate_service_config("chat", llm_provider, llm_model, llm_usage_mode)
        self._validate_service_config("transcription", transcription_provider, transcription_model, transcription_usage_mode)
        config = self.get_ai_config(user_id)
        config.llm_usage_mode = AIUsageMode(llm_usage_mode)
        config.llm_provider = ProviderType(llm_provider)
        config.llm_model = llm_model
        config.transcription_usage_mode = AIUsageMode(transcription_usage_mode)
        config.transcription_provider = ProviderType(transcription_provider)
        config.transcription_model = transcription_model
        config.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return config

    def test_credential(self, provider: str, api_key: str | None = None, user_id: int | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
        if not provider_enabled(provider):
            return {"valid": False, "provider": provider, "message": "Provider is not enabled."}
        saved_credential = self.get_credential(user_id, provider) if user_id is not None else None
        if not api_key and user_id is not None:
            api_key = self.get_decrypted_credential(user_id, provider)
        if not config and user_id is not None:
            config = self.get_credential_config(user_id, provider)
        if not api_key:
            return {"valid": False, "provider": provider, "message": "API key is missing."}
        try:
            if provider == "mailgun":
                self._test_provider_connection(provider, api_key, config or {})
            else:
                self._test_provider_connection(provider, api_key)
            result = {"valid": True, "provider": provider, "message": "Connection verified."}
        except Exception as exc:
            message = str(exc).strip() or "Connection failed."
            result = {"valid": False, "provider": provider, "message": message[:300]}
        if saved_credential is not None:
            saved_credential.is_valid = result["valid"]
            saved_credential.last_tested_at = datetime.now(timezone.utc)
            saved_credential.last_test_error = None if result["valid"] else result["message"]
            self.db.flush()
        return result

    @staticmethod
    def _test_provider_connection(provider: str, api_key: str, config: dict[str, Any] | None = None) -> None:
        if provider == "openai":
            OpenAI(api_key=api_key, timeout=15, max_retries=0).models.list()
            return
        if provider == "openrouter":
            response = httpx.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            response.raise_for_status()
            return
        if provider == "resend":
            response = httpx.get("https://api.resend.com/domains", headers={"Authorization": f"Bearer {api_key}"}, timeout=15)
            response.raise_for_status()
            return
        if provider == "mailgun":
            domain = (config or {}).get("domain")
            if not domain:
                raise ValueError("Mailgun domain is required.")
            response = httpx.get(f"https://api.mailgun.net/v3/{domain}", auth=("api", api_key), timeout=15)
            response.raise_for_status()
            return
        raise ValueError("Connection testing is not available for this provider.")

    def resolve_llm_config(self, user_id: int, override: dict[str, Any] | None = None) -> dict[str, Any]:
        config = self.get_ai_config(user_id)
        return self._resolve(
            user_id,
            service_type="llm",
            capability="chat",
            usage_mode=(override or {}).get("llm_usage_mode") or config.llm_usage_mode.value,
            provider=(override or {}).get("llm_provider") or config.llm_provider.value,
            model=(override or {}).get("llm_model") or config.llm_model,
        )

    def resolve_transcription_config(self, user_id: int, override: dict[str, Any] | None = None) -> dict[str, Any]:
        config = self.get_ai_config(user_id)
        return self._resolve(
            user_id,
            service_type="transcription",
            capability="transcription",
            usage_mode=(override or {}).get("transcription_usage_mode") or config.transcription_usage_mode.value,
            provider=(override or {}).get("transcription_provider") or config.transcription_provider.value,
            model=(override or {}).get("transcription_model") or config.transcription_model,
        )

    def _resolve(self, user_id: int, *, service_type: str, capability: str, usage_mode: str, provider: str, model: str | None) -> dict[str, Any]:
        self._validate_service_config(capability, provider, model, usage_mode)
        api_key = None
        if usage_mode == AIUsageMode.BYOK.value:
            api_key = self.get_decrypted_credential(user_id, provider)
            if not api_key:
                raise ValidationError(f"Your {provider} API key is missing.", code="INVALID_PROVIDER_CREDENTIALS")
        else:
            api_key = self._platform_api_key(provider)
            if not api_key:
                raise ValidationError(f"Application credentials for {provider} are not configured.", code="PROVIDER_UNAVAILABLE")
            credits = self.db.query(UserCredits).filter_by(user_id=user_id).first()
            if not credits or credits.balance <= 0:
                raise InsufficientCreditsError("You do not have enough credits to process this meeting.")
        return {"service_type": service_type, "usage_mode": usage_mode, "provider": provider, "model": model, "api_key": api_key}

    @staticmethod
    def _platform_api_key(provider: str) -> str | None:
        settings = Settings()
        if provider == "openai":
            return settings.openai_api_key
        if provider == "openrouter":
            return settings.openrouter_api_key
        return None

    @staticmethod
    def _validate_service_config(capability: str, provider: str, model: str | None, usage_mode: str) -> None:
        if usage_mode not in {AIUsageMode.APP_CREDITS.value, AIUsageMode.BYOK.value}:
            raise ValidationError("Invalid usage mode.", code="VALIDATION_ERROR")
        if not provider_supports(provider, capability):
            raise ValidationError(f"{provider} does not support {capability}.", code="INVALID_PROVIDER")
        if not provider_enabled(provider):
            raise ValidationError(f"{provider} is not enabled.", code="INVALID_PROVIDER")
        if not validate_model(provider, capability, model):
            models = [item["id"] for item in get_available_models(provider, capability)]
            raise ValidationError("Model is not supported by the selected provider.", code="UNSUPPORTED_MODEL", details={"supported_models": models})
