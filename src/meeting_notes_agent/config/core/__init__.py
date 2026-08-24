"""Core module for Meeting Notes API."""
from meeting_notes_agent.config.core.config import settings
from meeting_notes_agent.config.core.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    FileUploadError,
    InsufficientCreditsError,
    NotFoundError,
    ProcessingError,
    QuotaExceededError,
    ValidationError,
    to_http_exception,
)
from meeting_notes_agent.config.core.logging import get_logger, setup_logging

__all__ = [
    "settings",
    "setup_logging",
    "get_logger",
    "APIError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "QuotaExceededError",
    "InsufficientCreditsError",
    "ProcessingError",
    "FileUploadError",
    "to_http_exception",
]