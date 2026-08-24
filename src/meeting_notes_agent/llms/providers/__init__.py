"""Central LLM and transcription provider factories."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain_openai import ChatOpenAI
from openai import OpenAI

from meeting_notes_agent.config.core.config import Settings
from meeting_notes_agent.database import SessionLocal
from meeting_notes_agent.services.ai_settings_service import AISettingsService
from meeting_notes_agent.services.meeting_override_service import MeetingOverrideService


def _meeting_override(db, meeting_id: str | None, user_id: int | None) -> dict | None:
    if not meeting_id or user_id is None:
        return None
    try:
        from uuid import UUID
        return MeetingOverrideService(db).to_dict(UUID(meeting_id), user_id)
    except Exception:
        return None


def resolve_runtime_llm(state: Any) -> dict[str, Any]:
    db = SessionLocal()
    try:
        user_id = getattr(state, "user_id", None)
        if user_id is None:
            settings = Settings()
            return {
                "provider": "openai",
                "model": settings.openai_chat_model,
                "api_key": settings.openai_api_key,
                "usage_mode": "app_credits",
            }
        configuration = getattr(state, "configuration", None)
        if configuration is not None:
            selected = configuration.ai
            return AISettingsService(db)._resolve(
                user_id,
                service_type="llm",
                capability="chat",
                usage_mode=selected.usage_mode,
                provider=selected.provider,
                model=selected.model,
            )
        return AISettingsService(db).resolve_llm_config(user_id, _meeting_override(db, getattr(state, "meeting_id", None), user_id))
    finally:
        db.close()


def resolve_runtime_transcription(state: Any) -> dict[str, Any]:
    db = SessionLocal()
    try:
        user_id = getattr(state, "user_id", None)
        if user_id is None:
            settings = Settings()
            return {
                "provider": "openai",
                "model": settings.openai_transcription_model,
                "api_key": settings.openai_api_key,
                "usage_mode": "app_credits",
            }
        configuration = getattr(state, "configuration", None)
        if configuration is not None:
            selected = configuration.transcription
            return AISettingsService(db)._resolve(
                user_id,
                service_type="transcription",
                capability="transcription",
                usage_mode=selected.usage_mode,
                provider=selected.provider,
                model=selected.model,
            )
        return AISettingsService(db).resolve_transcription_config(user_id, _meeting_override(db, getattr(state, "meeting_id", None), user_id))
    finally:
        db.close()


def get_chat_llm_for_state(state: Any):
    resolved = resolve_runtime_llm(state)
    provider = resolved["provider"]
    configuration = getattr(state, "configuration", None)
    temperature = configuration.ai.temperature if configuration is not None else 0
    max_tokens = configuration.ai.max_output_tokens if configuration is not None else None
    if provider == "openai":
        return ChatOpenAI(
            model=resolved["model"],
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=resolved["api_key"],
            timeout=float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "60")),
            max_retries=0,
        )
    if provider == "openrouter":
        from langchain_openrouter import ChatOpenRouter

        return ChatOpenRouter(
            model=resolved["model"],
            api_key=resolved["api_key"],
            temperature=temperature,
            max_tokens=max_tokens,
        )
    raise RuntimeError(f"Provider {provider} is not implemented for chat")


def transcribe_file_for_state(state: Any, audio_path: Path) -> str:
    resolved = resolve_runtime_transcription(state)
    if resolved["provider"] != "openai":
        raise RuntimeError(f"Provider {resolved['provider']} is not implemented for transcription")
    client = OpenAI(
        api_key=resolved["api_key"],
        max_retries=0,
        timeout=float(os.environ.get("OPENAI_TRANSCRIPTION_TIMEOUT_SECONDS", "180")),
    )
    configuration = getattr(state, "configuration", None)
    language = configuration.transcription.language if configuration is not None else "auto"
    request = {"model": resolved["model"]}
    if language and language != "auto":
        request["language"] = language
    with audio_path.open("rb") as audio_file:
        result = client.audio.transcriptions.create(file=audio_file, **request)
    return result.text
