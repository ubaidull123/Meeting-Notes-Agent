"""AI Configuration database models."""
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint,
    func, JSON, Enum as SQLEnum, Boolean
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from meeting_notes_agent.database.models import Base


class ProviderType(str, PyEnum):
    OPENAI = "openai"
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    RESEND = "resend"
    MAILGUN = "mailgun"
    SMTP = "smtp"


class AIUsageMode(str, PyEnum):
    APP_CREDITS = "app_credits"
    BYOK = "byok"


class UserAIConfig(Base):
    """Per-user LLM and transcription defaults."""
    __tablename__ = "user_ai_config"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    # LLM settings
    llm_usage_mode = Column(SQLEnum(AIUsageMode), default=AIUsageMode.APP_CREDITS, nullable=False)
    llm_provider = Column(SQLEnum(ProviderType), default=ProviderType.OPENAI, nullable=False)
    llm_model = Column(String(100), nullable=True)
    llm_credential_id = Column(Integer, ForeignKey("user_credentials.id", ondelete="SET NULL"), nullable=True)

    # Transcription settings
    transcription_usage_mode = Column(SQLEnum(AIUsageMode), default=AIUsageMode.APP_CREDITS, nullable=False)
    transcription_provider = Column(SQLEnum(ProviderType), default=ProviderType.OPENAI, nullable=False)
    transcription_model = Column(String(100), nullable=True)
    transcription_credential_id = Column(Integer, ForeignKey("user_credentials.id", ondelete="SET NULL"), nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    user = relationship("User", back_populates="ai_config")


class UserCredential(Base):
    """Encrypted API credentials per user per provider."""
    __tablename__ = "user_credentials"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(SQLEnum(ProviderType), nullable=False, index=True)
    # Encrypted fields
    api_key_encrypted = Column(Text, nullable=True)  # AES-GCM encrypted
    api_key_hint = Column(String(20), nullable=True)  # Last 4 chars for display
    # Optional additional config (e.g., SMTP host/port)
    config_encrypted = Column(Text, nullable=True)  # JSON encrypted
    is_valid = Column(Boolean, default=False, nullable=False)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="credentials")
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_credential_user_provider"),)


class UserEmailConfig(Base):
    """Per-user email configuration."""
    __tablename__ = "user_email_config"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    email_mode = Column(SQLEnum(AIUsageMode), default=AIUsageMode.APP_CREDITS, nullable=False)
    provider = Column(SQLEnum(ProviderType), default=ProviderType.RESEND, nullable=False)
    sender_name = Column(String(255), nullable=True)
    sender_email = Column(String(255), nullable=True)
    reply_to_email = Column(String(255), nullable=True)
    credential_id = Column(Integer, ForeignKey("user_credentials.id", ondelete="SET NULL"), nullable=True)
    # SMTP specific
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_username = Column(String(255), nullable=True)
    smtp_use_tls = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    user = relationship("User", back_populates="email_config")


class CreditTransaction(Base):
    """Auditable credit ledger."""
    __tablename__ = "credit_transactions"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    meeting_id = Column(PGUUID(as_uuid=True), ForeignKey("meetings.id", ondelete="SET NULL"), nullable=True, index=True)
    amount = Column(Integer, nullable=False)  # positive = credit, negative = debit
    balance_after = Column(Integer, nullable=False)
    transaction_type = Column(String(50), nullable=False)  # "meeting_processing", "admin_adjustment", "refund"
    service_type = Column(String(50), nullable=True)  # "llm", "transcription", "email"
    provider = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    usage_mode = Column(SQLEnum(AIUsageMode), nullable=True)  # BYOK vs app credits
    usage_metadata = Column(JSON, nullable=True)  # tokens, duration, etc.
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UsageRecord(Base):
    """Detailed usage tracking per meeting per service."""
    __tablename__ = "usage_records"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    meeting_id = Column(PGUUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    service_type = Column(String(50), nullable=False)  # "llm", "transcription", "email"
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    usage_mode = Column(SQLEnum(AIUsageMode), nullable=False)  # BYOK or app_credits
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    audio_duration_seconds = Column(Integer, default=0)
    credits_cost = Column(Integer, default=0)
    status = Column(String(50), default="completed", nullable=False)  # completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MeetingAIOverride(Base):
    """Per-meeting AI provider/model overrides."""
    __tablename__ = "meeting_ai_overrides"
    meeting_id = Column(PGUUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # LLM overrides
    llm_usage_mode = Column(SQLEnum(AIUsageMode), nullable=True)
    llm_provider = Column(SQLEnum(ProviderType), nullable=True)
    llm_model = Column(String(100), nullable=True)
    # Transcription overrides
    transcription_usage_mode = Column(SQLEnum(AIUsageMode), nullable=True)
    transcription_provider = Column(SQLEnum(ProviderType), nullable=True)
    transcription_model = Column(String(100), nullable=True)
    # Email overrides
    email_mode = Column(SQLEnum(AIUsageMode), nullable=True)
    email_provider = Column(SQLEnum(ProviderType), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    meeting = relationship("Meeting", back_populates="ai_override")
    user = relationship("User", back_populates="ai_overrides")


class PricingRule(Base):
    """Configurable credit pricing per provider/model."""
    __tablename__ = "pricing_rules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    service_type = Column(String(50), nullable=False)  # "llm", "transcription"
    # Token-based pricing (per 1K tokens)
    input_token_price = Column(Integer, default=0)  # credits per 1K input tokens
    output_token_price = Column(Integer, default=0)  # credits per 1K output tokens
    # Audio pricing (per minute)
    audio_minute_price = Column(Integer, default=0)  # credits per minute
    # Flat fee per request
    flat_fee = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    __table_args__ = (UniqueConstraint("provider", "model", "service_type", name="uq_pricing_provider_model_service"),)