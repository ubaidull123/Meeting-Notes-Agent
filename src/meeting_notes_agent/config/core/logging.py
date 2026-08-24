"""Logging configuration for the Meeting Notes API."""
import logging
import sys
from typing import Any
from pythonjsonlogger import jsonlogger

from meeting_notes_agent.config.core.config import settings


class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from logs."""

    SENSITIVE_KEYS = {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "secret",
        "jwt_secret",
        "database_url",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and isinstance(record.msg, dict):
            self._sanitize_dict(record.msg)
        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                self._sanitize_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._sanitize_value(arg) if isinstance(arg, dict) else arg
                    for arg in record.args
                )
        return True

    def _sanitize_dict(self, data: dict) -> None:
        for key in list(data.keys()):
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                data[key] = "***REDACTED***"
            elif isinstance(data[key], dict):
                self._sanitize_dict(data[key])

    def _sanitize_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            self._sanitize_dict(value)
            return value
        return value


def setup_logging() -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if settings.debug else logging.INFO

    # Create formatters
    if settings.environment == "production":
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            timestamp=True,
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [console_handler]

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    # These clients can include full prompts, transcripts, or SQL parameters
    # in DEBUG/INFO records. Keep meeting content out of application logs.
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("langsmith").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
