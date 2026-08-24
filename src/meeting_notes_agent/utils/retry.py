"""Retry utilities for LLM calls and API operations."""
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
    after_log,
)
import logging
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar("T")


def is_retryable_llm_error(exc: Exception) -> bool:
    """Determine if an LLM error is retryable."""
    # Check for common retryable error patterns
    message = str(exc).lower()

    # Rate limiting
    if any(keyword in message for keyword in ["rate limit", "429", "too many requests", "quota exceeded"]):
        return True

    # Server errors
    if any(keyword in message for keyword in ["500", "502", "503", "504", "internal server error", "bad gateway", "service unavailable", "gateway timeout"]):
        return True

    # Timeout/connection errors
    if any(keyword in message for keyword in ["timeout", "timed out", "connection error", "connection refused", "connection reset", "dns", "network"]):
        return True

    # Temporary API issues
    if any(keyword in message for keyword in ["temporarily unavailable", "try again", "overloaded"]):
        return True

    # Specific OpenAI/LangChain exceptions
    retryable_types = (
        "APITimeoutError",
        "APIConnectionError",
        "InternalServerError",
        "RateLimitError",
    )
    if any(t in type(exc).__name__ for t in retryable_types):
        return True

    return False


def is_retryable_email_error(exc: Exception) -> bool:
    """Determine if an email error is retryable."""
    return is_retryable_llm_error(exc)  # Same logic for HTTP APIs


def get_llm_retry_decorator(
    max_attempts: int = 3,
    base_wait: float = 1.0,
    max_wait: float = 30.0,
):
    """
    Get a retry decorator for LLM calls.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        base_wait: Base wait time in seconds (default: 1.0)
        max_wait: Maximum wait time in seconds (default: 30.0)
    """
    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_wait, min=base_wait, max=max_wait),
        retry=retry_if_exception(is_retryable_llm_error),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
    )


def get_email_retry_decorator(
    max_attempts: int = 3,
    base_wait: float = 2.0,
    max_wait: float = 60.0,
):
    """
    Get a retry decorator for email sending.

    Args:
        max_attempts: Maximum number of attempts (default: 3)
        base_wait: Base wait time in seconds (default: 2.0)
        max_wait: Maximum wait time in seconds (default: 60.0)
    """
    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=base_wait, min=base_wait, max=max_wait),
        retry=retry_if_exception(is_retryable_email_error),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
    )


# Pre-configured decorators for common use cases
llm_retry = get_llm_retry_decorator(max_attempts=3, base_wait=1.0, max_wait=30.0)
email_retry = get_email_retry_decorator(max_attempts=3, base_wait=2.0, max_wait=60.0)
