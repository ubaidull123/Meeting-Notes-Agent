"""Tests for safe, refreshable OpenAI configuration and retry behavior."""
import pytest

from meeting_notes_agent.llms.API_Based.openai import get_openai_api_key
from meeting_notes_agent.utils.retry import get_llm_retry_decorator


def test_api_key_uses_injected_value_in_test_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-value-that-is-long-enough-for-unit-tests")

    assert get_openai_api_key() == "sk-test-value-that-is-long-enough-for-unit-tests"


def test_api_key_rejects_placeholder(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-dummy-replacement")

    with pytest.raises(RuntimeError, match="placeholder"):
        get_openai_api_key()


def test_authentication_errors_are_not_retried():
    attempts = 0

    @get_llm_retry_decorator(max_attempts=3, base_wait=0, max_wait=0)
    def fail_with_invalid_key():
        nonlocal attempts
        attempts += 1
        raise RuntimeError("401 invalid_api_key")

    with pytest.raises(RuntimeError, match="invalid_api_key"):
        fail_with_invalid_key()

    assert attempts == 1
