"""Full-stack backend coverage for user-configurable AI platform settings."""
from datetime import date
from uuid import uuid4

import pytest

from meeting_notes_agent.auth.security import hash_password
from meeting_notes_agent.config.core.exceptions import InsufficientCreditsError, ValidationError
from meeting_notes_agent.database.models import Meeting, MeetingStatus, User, UserRole
from meeting_notes_agent.database.models_ai_config import AIUsageMode, UserCredential
from meeting_notes_agent.database.repositories import UserCreditsRepository
from meeting_notes_agent.services.ai_settings_service import AISettingsService
from meeting_notes_agent.services.processing_service import ProcessingService


def test_settings_api_crud_masks_and_deletes_credentials(client, auth_headers, db_session, test_user):
    catalog = client.get("/api/v1/settings/providers", headers=auth_headers)
    assert catalog.status_code == 200
    assert "openai" in catalog.json()

    response = client.put(
        "/api/v1/settings/ai",
        headers=auth_headers,
        json={
            "llm_usage_mode": "byok",
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini",
            "transcription_usage_mode": "app_credits",
            "transcription_provider": "openai",
            "transcription_model": "gpt-4o-mini-transcribe",
        },
    )
    assert response.status_code == 200
    assert response.json()["llm_usage_mode"] == "byok"

    saved = client.post(
        "/api/v1/settings/credentials",
        headers=auth_headers,
        json={"provider": "openai", "api_key": "sk-test-secret-abcd"},
    )
    assert saved.status_code == 201
    body = saved.json()
    assert body["has_api_key"] is True
    assert body["api_key_hint"].endswith("abcd")
    assert "sk-test-secret" not in saved.text

    stored = db_session.query(UserCredential).filter_by(user_id=test_user.id).first()
    assert stored is not None
    assert stored.api_key_encrypted != "sk-test-secret-abcd"

    listed = client.get("/api/v1/settings/credentials", headers=auth_headers)
    assert listed.status_code == 200
    assert "sk-test-secret" not in listed.text

    deleted = client.delete("/api/v1/settings/credentials/openai", headers=auth_headers)
    assert deleted.status_code == 204
    assert db_session.query(UserCredential).filter_by(user_id=test_user.id).first() is None


def test_user_a_cannot_see_user_b_credentials(client, auth_headers, db_session):
    user_b = User(
        email="other@example.com",
        password_hash=hash_password("TestPass123!"),
        full_name="Other User",
        role=UserRole.USER,
    )
    db_session.add(user_b)
    db_session.commit()

    AISettingsService(db_session).save_credential(user_b.id, "openai", "sk-other-secret-9999")
    db_session.commit()

    response = client.get("/api/v1/settings/credentials", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []
    assert "sk-other-secret" not in response.text


def test_invalid_provider_model_rejected(client, auth_headers):
    response = client.put(
        "/api/v1/settings/ai",
        headers=auth_headers,
        json={
            "llm_usage_mode": "app_credits",
            "llm_provider": "openai",
            "llm_model": "not-a-real-model",
            "transcription_usage_mode": "app_credits",
            "transcription_provider": "openai",
            "transcription_model": "gpt-4o-mini-transcribe",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "UNSUPPORTED_MODEL"


def test_byok_resolution_requires_key_and_does_not_spend_app_credits(db_session, test_user):
    service = AISettingsService(db_session)
    service.update_ai_config(
        test_user.id,
        llm_usage_mode="byok",
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        transcription_usage_mode="app_credits",
        transcription_provider="openai",
        transcription_model="gpt-4o-mini-transcribe",
    )
    db_session.commit()

    with pytest.raises(ValidationError, match="API key is missing"):
        service.resolve_llm_config(test_user.id)

    service.save_credential(test_user.id, "openai", "sk-user-key-abcd")
    credits = UserCreditsRepository(db_session).get_or_create(test_user.id)
    credits.balance = 10
    meeting = Meeting(
        id=uuid4(),
        user_id=test_user.id,
        team_id=test_user.team_memberships[0].team_id,
        created_by=test_user.id,
        title="BYOK meeting",
        meeting_date=date.today(),
        transcript_text="Transcript",
        tokens_used=50,
        status=MeetingStatus.COMPLETED,
    )
    db_session.add(meeting)
    db_session.flush()

    ProcessingService._record_terminal_processing_usage(db_session, meeting)
    db_session.commit()
    db_session.refresh(credits)

    assert credits.balance == 10
    assert meeting.credits_charged is True


def test_app_credit_processing_deducts_and_logs_usage(db_session, test_user):
    ProcessingService._ensure_processing_allowance(db_session, test_user.id)
    credits = UserCreditsRepository(db_session).get_by_user_id(test_user.id)
    assert credits.balance == 500

    meeting = Meeting(
        id=uuid4(),
        user_id=test_user.id,
        team_id=test_user.team_memberships[0].team_id,
        created_by=test_user.id,
        title="Credit meeting",
        meeting_date=date.today(),
        transcript_text="Transcript",
        tokens_used=33,
        status=MeetingStatus.COMPLETED,
    )
    db_session.add(meeting)
    db_session.flush()

    ProcessingService._record_terminal_processing_usage(db_session, meeting)
    db_session.commit()
    db_session.refresh(credits)

    assert credits.balance == 499
    usage = client_rows(db_session, "usage_records", test_user.id)
    transactions = client_rows(db_session, "credit_transactions", test_user.id)
    assert len(usage) == 1
    assert usage[0].service_type == "llm"
    assert usage[0].usage_mode == AIUsageMode.APP_CREDITS
    assert len(transactions) == 1
    assert transactions[0].amount == -1


def test_insufficient_app_credits_blocks_cleanly(db_session, test_user):
    ProcessingService._ensure_processing_allowance(db_session, test_user.id)
    credits = UserCreditsRepository(db_session).get_by_user_id(test_user.id)
    credits.balance = 0
    meeting = Meeting(
        id=uuid4(),
        user_id=test_user.id,
        team_id=test_user.team_memberships[0].team_id,
        created_by=test_user.id,
        title="Blocked meeting",
        meeting_date=date.today(),
        transcript_text="Transcript",
        status=MeetingStatus.DRAFT,
    )
    db_session.add(meeting)
    db_session.commit()

    with pytest.raises(InsufficientCreditsError) as exc:
        ProcessingService._ensure_processing_allowance(db_session, test_user.id, meeting)
    assert exc.value.code == "INSUFFICIENT_CREDITS"


def test_email_settings_initial_load(client, auth_headers):
    response = client.get("/api/v1/settings/email", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "email_mode": "app_credits",
        "provider": "resend",
        "sender_name": None,
        "sender_email": None,
        "reply_to_email": None,
        "sending_domain": None,
        "domain_status": None,
        "smtp_host": None,
        "smtp_port": None,
        "smtp_username": None,
        "smtp_use_tls": True,
    }


def test_email_settings_api(client, auth_headers):
    response = client.put(
        "/api/v1/settings/email",
        headers=auth_headers,
        json={
            "email_mode": "app_credits",
            "provider": "resend",
            "sender_name": "Meetings",
            "sender_email": "meetings@example.com",
            "reply_to_email": "reply@example.com",
            "smtp_use_tls": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sender_email"] == "meetings@example.com"
    assert body["sending_domain"] == "example.com"
    assert body["domain_status"] == "configured"


def test_email_byok_resend_uses_user_credential(db_session, test_user, monkeypatch):
    from meeting_notes_agent.Nodes.send_email import send_email_node
    from meeting_notes_agent.database.models_ai_config import ProviderType, UserEmailConfig
    from meeting_notes_agent.state_schema import Attendee, MeetingState

    sent_keys = []

    def fake_send(params):
        import resend

        sent_keys.append(resend.api_key)
        return {"id": "email-id"}

    monkeypatch.setattr("resend.Emails.send", fake_send)
    monkeypatch.setenv("RESEND_FROM_EMAIL", "Meeting Notes <notes@verified.example>")
    AISettingsService(db_session).save_credential(test_user.id, "resend", "re_user_key_1234")
    db_session.add(
        UserEmailConfig(
            user_id=test_user.id,
            email_mode=AIUsageMode.BYOK,
            provider=ProviderType.RESEND,
            sender_name="Meetings",
            sender_email="notes@verified.example",
        )
    )
    db_session.commit()

    state = MeetingState(
        user_id=test_user.id,
        meeting_title="Email BYOK",
        transcript_text="Transcript",
        attendees=[Attendee(name="A", email="a@example.com")],
        redacted_summary="Summary",
        email_draft="Reviewed email",
    )
    result = send_email_node(state)

    assert result["email_sent"] is True
    assert sent_keys == ["re_user_key_1234"]


def client_rows(db_session, table_name: str, user_id: int):
    from meeting_notes_agent.database.models_ai_config import CreditTransaction, UsageRecord

    model = UsageRecord if table_name == "usage_records" else CreditTransaction
    return db_session.query(model).filter_by(user_id=user_id).all()
