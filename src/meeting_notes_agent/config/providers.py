"""Backend-owned provider/model catalog."""
from __future__ import annotations

from typing import Any


PROVIDER_CATALOG: dict[str, dict[str, Any]] = {
    "openai": {
        "name": "OpenAI",
        "enabled": True,
        "capabilities": ["chat", "transcription"],
        "models": {
            "chat": [
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o mini",
                    "tier": "economy",
                    "speed": "fast",
                    "quality": "good",
                    "recommended_for": "Routine meeting summaries and drafts.",
                },
                {
                    "id": "gpt-4.1-mini",
                    "name": "GPT-4.1 mini",
                    "tier": "balanced",
                    "speed": "fast",
                    "quality": "strong",
                    "recommended_for": "More detailed reasoning over longer meetings.",
                },
            ],
            "transcription": [
                {
                    "id": "gpt-4o-mini-transcribe",
                    "name": "GPT-4o mini transcribe",
                    "tier": "balanced",
                    "speed": "fast",
                    "quality": "strong",
                    "recommended_for": "Meeting audio transcription.",
                },
                {
                    "id": "whisper-1",
                    "name": "Whisper",
                    "tier": "economy",
                    "speed": "standard",
                    "quality": "good",
                    "recommended_for": "Reliable baseline transcription.",
                },
            ],
        },
    },
    "openrouter": {
        "name": "OpenRouter",
        "enabled": True,
        "capabilities": ["chat"],
        "models": {
            "chat": [
                {
                    "id": "openai/gpt-4o-mini",
                    "name": "OpenAI GPT-4o mini via OpenRouter",
                    "tier": "balanced",
                    "speed": "fast",
                    "quality": "good",
                    "recommended_for": "OpenRouter-backed meeting summaries.",
                },
            ]
        },
    },
    "groq": {"name": "Groq", "enabled": False, "capabilities": ["chat"], "models": {"chat": []}},
    "anthropic": {"name": "Anthropic", "enabled": False, "capabilities": ["chat"], "models": {"chat": []}},
    "gemini": {"name": "Google Gemini", "enabled": False, "capabilities": ["chat"], "models": {"chat": []}},
    "resend": {"name": "Resend", "enabled": True, "capabilities": ["email"], "models": {}},
    "mailgun": {"name": "Mailgun", "enabled": True, "capabilities": ["email"], "models": {}},
    "smtp": {"name": "SMTP", "enabled": False, "capabilities": ["email"], "models": {}},
}


def get_available_providers(capability: str) -> dict[str, dict[str, Any]]:
    return {
        key: value
        for key, value in PROVIDER_CATALOG.items()
        if capability in value.get("capabilities", [])
    }


def provider_supports(provider: str, capability: str) -> bool:
    return capability in PROVIDER_CATALOG.get(provider, {}).get("capabilities", [])


def provider_enabled(provider: str) -> bool:
    return bool(PROVIDER_CATALOG.get(provider, {}).get("enabled"))


def get_available_models(provider: str, capability: str) -> list[dict[str, Any]]:
    return PROVIDER_CATALOG.get(provider, {}).get("models", {}).get(capability, [])


def validate_model(provider: str, capability: str, model: str | None) -> bool:
    if capability == "email":
        return True
    return bool(model) and any(item["id"] == model for item in get_available_models(provider, capability))
