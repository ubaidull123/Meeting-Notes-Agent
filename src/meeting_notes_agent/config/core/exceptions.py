"""Custom exceptions for the Meeting Notes API."""
from typing import Any, Optional
from fastapi import HTTPException, status


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON shape used by API exception handlers."""
        payload: dict[str, Any] = {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class AuthenticationError(APIError):
    """Authentication related errors."""

    def __init__(self, message: str = "Authentication failed", code: str = "AUTHENTICATION_ERROR", details: Optional[dict] = None):
        super().__init__(message, code, status.HTTP_401_UNAUTHORIZED, details)


class AuthorizationError(APIError):
    """Authorization related errors."""

    def __init__(self, message: str = "Not authorized", code: str = "AUTHORIZATION_ERROR", details: Optional[dict] = None):
        super().__init__(message, code, status.HTTP_403_FORBIDDEN, details)


class ValidationError(APIError):
    """Validation errors."""

    def __init__(self, message: str = "Validation failed", code: str = "VALIDATION_ERROR", details: Optional[dict] = None):
        super().__init__(message, code, status.HTTP_422_UNPROCESSABLE_CONTENT, details)


class NotFoundError(APIError):
    """Resource not found errors."""

    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND", details: Optional[dict] = None):
        super().__init__(message, code, status.HTTP_404_NOT_FOUND, details)


class ConflictError(APIError):
    """Conflict errors (e.g., duplicate resource)."""

    def __init__(self, message: str = "Resource conflict", code: str = "CONFLICT", details: Optional[dict] = None):
        super().__init__(message, code, status.HTTP_409_CONFLICT, details)


class QuotaExceededError(APIError):
    """Quota exceeded errors."""

    def __init__(self, message: str = "Quota exceeded", code: str = "QUOTA_EXCEEDED", details: Optional[dict] = None):
        super().__init__(message, code, status.HTTP_403_FORBIDDEN, details)


class InsufficientCreditsError(APIError):
    """Insufficient credits errors."""

    def __init__(self, message: str = "Insufficient credits", code: str = "INSUFFICIENT_CREDITS", details: Optional[dict] = None):
        super().__init__(message, code, status.HTTP_403_FORBIDDEN, details)


class ProcessingError(APIError):
    """Meeting processing errors."""

    def __init__(self, message: str = "Processing failed", code: str = "PROCESSING_ERROR", details: Optional[dict] = None):
        super().__init__(message, code, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class ProcessingCancelled(Exception):
    """Internal signal raised when a running meeting is cancelled."""


class FileUploadError(APIError):
    """File upload errors."""

    def __init__(self, message: str = "File upload failed", code: str = "FILE_UPLOAD_ERROR", details: Optional[dict] = None):
        super().__init__(message, code, status.HTTP_413_PAYLOAD_TOO_LARGE, details)


def to_http_exception(error: APIError) -> HTTPException:
    """Convert APIError to FastAPI HTTPException."""
    return HTTPException(
        status_code=error.status_code,
        detail={
            "error": {
                "code": error.code,
                "message": error.message,
                **({"details": error.details} if error.details else {}),
            }
        },
    )
