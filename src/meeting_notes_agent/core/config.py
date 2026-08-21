"""Application configuration using Pydantic Settings."""
import json
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Environment
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database
    database_url: str = Field(alias="DATABASE_URL")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="meeting_notes", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")

    # JWT Authentication
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_refresh_secret_key: str = Field(alias="JWT_REFRESH_SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    algorithm: str = "HS256"

    # CORS - stored as comma-separated string in env
    cors_origins_raw: str = Field(default="http://localhost:5173,http://127.0.0.1:5173", alias="ALLOWED_ORIGINS")

    # LLM Providers
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")

    # Email delivery
    email_provider: str = Field(default="resend", alias="EMAIL_PROVIDER")

    # Mailgun Email
    mailgun_api_key: Optional[str] = Field(default=None, alias="MAILGUN_API_KEY")
    mailgun_domain: Optional[str] = Field(default=None, alias="MAILGUN_DOMAIN")
    mailgun_base_url: str = Field(default="https://api.mailgun.net", alias="MAILGUN_BASE_URL")
    mailgun_from_email: Optional[str] = Field(default=None, alias="MAILGUN_FROM_EMAIL")

    # Resend Email (kept as an optional alternative provider)
    resend_api_key: Optional[str] = Field(default=None, alias="RESEND_API_KEY")
    resend_from_email: str = Field(default="Meeting Notes <onboarding@resend.dev>", alias="RESEND_FROM_EMAIL")
    resend_test_recipient: Optional[str] = Field(default=None, alias="RESEND_TEST_RECIPIENT")

    # LangSmith
    langsmith_api_key: Optional[str] = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_tracing: bool = Field(default=True, alias="LANGSMITH_TRACING")
    langsmith_project: str = Field(default="meeting-notes-agent", alias="LANGSMITH_PROJECT")
    langsmith_endpoint: str = Field(default="https://api.smith.langchain.com", alias="LANGSMITH_ENDPOINT")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")

    # API Server
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    # File Upload
    max_upload_size_mb: int = Field(default=100, alias="MAX_UPLOAD_SIZE_MB")
    upload_dir: str = Field(default="data/uploads", alias="UPLOAD_DIR")

    # Local LangGraph persistence
    langgraph_checkpoint_db: str = Field(
        default="data/langgraph_checkpoints.sqlite",
        alias="LANGGRAPH_CHECKPOINT_DB",
    )

    @computed_field
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.cors_origins_raw:
            return []
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
