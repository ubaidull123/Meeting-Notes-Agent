import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from meeting_notes_agent.database.models import Base, User, UserRole
from meeting_notes_agent.database.models_ai_config import (
    UserAIConfig, UserCredential, UserEmailConfig, CreditTransaction,
    UsageRecord, MeetingAIOverride, PricingRule,
    ProviderType, AIUsageMode
)
from datetime import datetime, timezone

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_user_ai_config_creation(db_session):
    user = User(email="test@example.com", password_hash="hash", full_name="Test User", role=UserRole.USER)
    db_session.add(user)
    db_session.flush()

    config = UserAIConfig(
        user_id=user.id,
        llm_usage_mode=AIUsageMode.BYOK,
        llm_provider=ProviderType.OPENAI,
        llm_model="gpt-4o-mini",
        transcription_usage_mode=AIUsageMode.APP_CREDITS,
        transcription_provider=ProviderType.OPENAI,
        transcription_model="gpt-4o-mini-transcribe",
    )
    db_session.add(config)
    db_session.commit()

    saved = db_session.query(UserAIConfig).filter_by(user_id=user.id).first()
    assert saved.llm_usage_mode == AIUsageMode.BYOK
    assert saved.llm_provider == ProviderType.OPENAI
    assert saved.llm_model == "gpt-4o-mini"

def test_user_credential_encryption_fields(db_session):
    user = User(email="test2@example.com", password_hash="hash", full_name="Test User 2", role=UserRole.USER)
    db_session.add(user)
    db_session.flush()

    cred = UserCredential(
        user_id=user.id,
        provider=ProviderType.OPENAI,
        api_key_encrypted="encrypted_key_here",
        api_key_hint="••••abcd",
        is_valid=True,
    )
    db_session.add(cred)
    db_session.commit()

    saved = db_session.query(UserCredential).filter_by(user_id=user.id, provider=ProviderType.OPENAI).first()
    assert saved.api_key_hint == "••••abcd"
    assert saved.is_valid is True

def test_credit_transaction_ledger(db_session):
    user = User(email="test3@example.com", password_hash="hash", full_name="Test User 3", role=UserRole.USER)
    db_session.add(user)
    db_session.flush()

    tx = CreditTransaction(
        user_id=user.id,
        amount=-10,
        balance_after=90,
        transaction_type="meeting_processing",
        service_type="llm",
        provider="openai",
        model="gpt-4o-mini",
        usage_mode=AIUsageMode.APP_CREDITS,
        usage_metadata={"input_tokens": 1000, "output_tokens": 500},
        description="Meeting processing",
    )
    db_session.add(tx)
    db_session.commit()

    saved = db_session.query(CreditTransaction).filter_by(user_id=user.id).first()
    assert saved.amount == -10
    assert saved.balance_after == 90
    assert saved.usage_metadata["input_tokens"] == 1000

def test_pricing_rule_unique_constraint(db_session):
    rule1 = PricingRule(provider="openai", model="gpt-4o-mini", service_type="llm",
                        input_token_price=1, output_token_price=2)
    rule2 = PricingRule(provider="openai", model="gpt-4o-mini", service_type="llm",
                        input_token_price=2, output_token_price=3)
    db_session.add(rule1)
    db_session.commit()

    db_session.add(rule2)
    with pytest.raises(Exception):  # IntegrityError
        db_session.commit()