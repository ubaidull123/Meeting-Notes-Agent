"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError, OperationalError

from meeting_notes_agent.config.core.config import settings
from meeting_notes_agent.config.core.exceptions import (
    APIError as BaseAppException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ConflictError,
    ProcessingError,
    QuotaExceededError,
    InsufficientCreditsError,
)
from meeting_notes_agent.database.session import init_db
from meeting_notes_agent.config.core.logging import setup_logging
from meeting_notes_agent.api.v1 import auth, users, meetings, tasks, admin, settings as settings_routes


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    logger.info("Starting Meeting Notes API...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down Meeting Notes API...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Meeting Notes API",
        description="REST API for meeting transcription, summarization, and action item extraction",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": "ValidationError",
                "message": "Request validation failed",
                "details": errors,
            },
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": "ValidationError",
                "message": "Request validation failed",
                "details": errors,
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.error(f"Database integrity error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "ConflictError",
                "message": "Database integrity constraint violation",
                "details": str(exc.orig) if settings.environment != "production" else "Conflict occurred",
            },
        )

    @app.exception_handler(OperationalError)
    async def operational_error_handler(request: Request, exc: OperationalError):
        logger.error(f"Database operational error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "ServiceUnavailableError",
                "message": "Database connection error",
                "details": "Service temporarily unavailable",
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "details": str(exc) if settings.environment != "production" else "Internal server error",
            },
        )

    # Include routers
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(meetings.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(settings_routes.router, prefix="/api/v1")

    # Health endpoints
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "meeting-notes-api",
            "version": "1.0.0",
        }

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check():
        """Readiness check endpoint."""
        # Check database connection
        from meeting_notes_agent.database.session import engine
        from sqlalchemy import text
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ready = True
        except Exception:
            db_ready = False

        return {
            "status": "ready" if db_ready else "not_ready",
            "database": "connected" if db_ready else "disconnected",
        }

    @app.get("/health/live", tags=["Health"])
    async def liveness_check():
        """Liveness check endpoint."""
        return {"status": "alive"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "meeting_notes_agent.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
