"""Vertical-slice tests for authenticated product settings."""
from meeting_notes_agent.auth.security import hash_password
from datetime import date
from uuid import uuid4

from meeting_notes_agent.database.models import Meeting, MeetingStatus, User, UserRole
from meeting_notes_agent.services.configuration_resolver import UserConfigurationResolver
from meeting_notes_agent.services.product_settings_service import ProductSettingsService
from meeting_notes_agent.state_schema import MeetingState, ResolvedMeetingConfiguration


def test_profile_settings_defaults_and_persist(client, auth_headers, db_session, test_user):
    initial = client.get("/api/v1/settings/profile", headers=auth_headers)
    assert initial.status_code == 200
    assert initial.json()["display_name"] == "Test User"
    assert initial.json()["timezone"] == "UTC"
    assert initial.json()["email"] == test_user.email

    updated = client.put(
        "/api/v1/settings/profile",
        headers=auth_headers,
        json={
            "display_name": "Ubaid Saeed",
            "timezone": "Asia/Karachi",
            "language": "en",
            "date_format": "dd-mm-yyyy",
            "time_format": "24h",
            "organization": "HEC",
            "job_title": "AI Engineer",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["organization"] == "HEC"

    db_session.expire_all()
    reloaded = client.get("/api/v1/settings/profile", headers=auth_headers)
    assert reloaded.status_code == 200
    assert reloaded.json()["display_name"] == "Ubaid Saeed"
    assert reloaded.json()["timezone"] == "Asia/Karachi"


def test_profile_settings_reject_invalid_values(client, auth_headers):
    response = client.put(
        "/api/v1/settings/profile",
        headers=auth_headers,
        json={
            "display_name": " ",
            "timezone": "Asia/Karachi",
            "language": "xx",
            "date_format": "dd-mm-yyyy",
            "time_format": "24h",
        },
    )
    assert response.status_code == 422


def test_profile_settings_are_isolated_by_authenticated_user(client, auth_headers, db_session):
    other = User(
        email="profile-other@example.com",
        password_hash=hash_password("TestPass123!"),
        full_name="Other User",
        role=UserRole.USER,
    )
    db_session.add(other)
    db_session.commit()

    response = client.get("/api/v1/settings/profile", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["display_name"] == "Test User"
    assert response.json()["email"] != other.email


def test_profile_settings_require_authentication(client):
    response = client.get("/api/v1/settings/profile")
    assert response.status_code == 401


def test_ai_advanced_and_transcription_settings_persist(client, auth_headers):
    ai = client.get("/api/v1/settings/ai", headers=auth_headers)
    assert ai.status_code == 200
    payload = ai.json()
    payload.update({"temperature": 0.6, "max_output_tokens": 2400, "response_language": "English"})
    updated_ai = client.put("/api/v1/settings/ai", headers=auth_headers, json=payload)
    assert updated_ai.status_code == 200
    assert updated_ai.json()["temperature"] == 0.6
    assert updated_ai.json()["max_output_tokens"] == 2400

    transcription = client.put(
        "/api/v1/settings/transcription",
        headers=auth_headers,
        json={
            "usage_mode": "app_credits",
            "provider": "openai",
            "model": "whisper-1",
            "language": "ur",
        },
    )
    assert transcription.status_code == 200
    assert transcription.json()["model"] == "whisper-1"
    assert transcription.json()["language"] == "ur"

    reloaded = client.get("/api/v1/settings/transcription", headers=auth_headers)
    assert reloaded.json()["language"] == "ur"


def test_saved_credential_is_unverified_until_connection_test(
    client,
    auth_headers,
    monkeypatch,
):
    saved = client.post(
        "/api/v1/settings/credentials",
        headers=auth_headers,
        json={"provider": "openai", "api_key": "sk-test-secret-abcd"},
    )
    assert saved.status_code == 201
    assert saved.json()["is_valid"] is False

    monkeypatch.setattr(
        "meeting_notes_agent.services.ai_settings_service.AISettingsService._test_provider_connection",
        staticmethod(lambda provider, api_key: None),
    )
    tested = client.post(
        "/api/v1/settings/credentials/test",
        headers=auth_headers,
        json={"provider": "openai"},
    )
    assert tested.status_code == 200
    assert tested.json()["valid"] is True

    listed = client.get("/api/v1/settings/credentials", headers=auth_headers)
    assert listed.json()[0]["is_valid"] is True


def test_meeting_defaults_persist_and_resolve_into_processing_state(
    client,
    auth_headers,
    db_session,
    test_user,
):
    payload = {
        "default_meeting_type": "planning",
        "generate_summary": True,
        "generate_action_items": False,
        "generate_decisions": True,
        "generate_insights": True,
        "generate_follow_up_email": False,
        "require_human_review": False,
        "require_email_approval": False,
        "redact_sensitive_information": False,
        "summary_style": "technical",
        "summary_sections": ["main_topics", "risks", "questions"],
        "custom_instructions": "Separate frontend and backend decisions.",
    }
    response = client.put("/api/v1/settings/meetings", headers=auth_headers, json=payload)
    assert response.status_code == 200

    meeting = Meeting(
        id=uuid4(),
        user_id=test_user.id,
        title="Configuration meeting",
        meeting_date=date.today(),
        transcript_text="Transcript",
        status=MeetingStatus.DRAFT,
    )
    db_session.add(meeting)
    db_session.commit()

    resolved = UserConfigurationResolver(db_session).resolve(test_user.id, meeting.id)
    assert resolved.generate_action_items is False
    assert resolved.require_human_review is False
    assert resolved.custom_instructions == "Separate frontend and backend decisions."


def test_meeting_defaults_change_graph_routes():
    from meeting_notes_agent.graph import route_after_email_draft, route_after_redaction, route_after_tasks

    configuration = ResolvedMeetingConfiguration(
        require_human_review=False,
        generate_follow_up_email=False,
        require_email_approval=False,
    )
    state = MeetingState(transcript_text="Transcript", configuration=configuration)
    assert route_after_redaction(state) == "continue"
    assert route_after_tasks(state) == "store"
    assert route_after_email_draft(state) == "send"


def test_redaction_can_be_disabled_without_calling_llm(monkeypatch):
    from meeting_notes_agent.Nodes.vi_redaction import redact_sensitive_info

    monkeypatch.setattr(
        "meeting_notes_agent.Nodes.vi_redaction._invoke_llm_with_retry",
        lambda *_: (_ for _ in ()).throw(AssertionError("LLM should not be called")),
    )
    state = MeetingState(
        transcript_text="Transcript",
        cleaned_transcription="Alice shared alice@example.com",
        summary="Summary",
        decisions=["Decision"],
        action_items=["Action"],
        configuration=ResolvedMeetingConfiguration(redact_sensitive_information=False),
    )
    result = redact_sensitive_info(state)
    assert result["redacted_transcription"] == state.cleaned_transcription
    assert result["redacted_summary"] == "Summary"


def test_summary_preferences_are_added_without_replacing_system_prompt(monkeypatch):
    from meeting_notes_agent.Nodes.iv_summerize import summarize_meeting_notes

    captured = {}

    class Result:
        content = "## Summary\nTechnical summary\n## Decisions Made\n- Decision\n## Action Items\n- Action"
        usage_metadata = {"total_tokens": 5}

    def fake_invoke(state, messages):
        captured["system"] = messages[0][1]
        return Result()

    monkeypatch.setattr("meeting_notes_agent.Nodes.iv_summerize._invoke_llm_with_retry", fake_invoke)
    state = MeetingState(
        transcript_text="Transcript",
        cleaned_transcription="Architecture discussion",
        configuration=ResolvedMeetingConfiguration(
            summary_style="technical",
            generate_action_items=False,
            custom_instructions="Highlight architecture decisions.",
        ),
    )
    result = summarize_meeting_notes(state)
    assert "meeting-notes summarizer" in captured["system"]
    assert "<user_meeting_instructions>" in captured["system"]
    assert result["action_items"] == []


def test_notification_and_privacy_foundations_persist(client, auth_headers):
    notifications = client.put(
        "/api/v1/settings/notifications",
        headers=auth_headers,
        json={
            "processing_finished": False,
            "processing_failed": True,
            "review_required": True,
            "email_approval_required": False,
            "credits_low": True,
        },
    )
    assert notifications.status_code == 200
    assert notifications.json()["processing_finished"] is False
    assert notifications.json()["delivery_available"] is False

    privacy = client.put(
        "/api/v1/settings/privacy",
        headers=auth_headers,
        json={"recording_retention": "7_days", "keep_transcript": False},
    )
    assert privacy.status_code == 200
    assert privacy.json()["recording_retention"] == "7_days"
    assert privacy.json()["automatic_cleanup_available"] is False


def test_usage_summary_and_rows_are_user_facing(client, auth_headers):
    summary = client.get("/api/v1/settings/usage/summary", headers=auth_headers)
    assert summary.status_code == 200
    assert summary.json()["balance"] == 500
    assert summary.json()["llm_requests"] == 0

    rows = client.get("/api/v1/settings/usage", headers=auth_headers)
    assert rows.status_code == 200
    assert rows.json() == []


def test_mailgun_configuration_is_encrypted_masked_and_resolved(
    client,
    auth_headers,
    db_session,
    test_user,
    monkeypatch,
):
    from meeting_notes_agent.database.models_ai_config import UserCredential
    from meeting_notes_agent.services.email_settings_service import EmailSettingsService

    saved = client.post(
        "/api/v1/settings/credentials",
        headers=auth_headers,
        json={
            "provider": "mailgun",
            "api_key": "key-private-mailgun-abcd",
            "config": {"domain": "mg.example.com"},
        },
    )
    assert saved.status_code == 201
    assert saved.json()["api_key_hint"].endswith("abcd")
    assert saved.json()["configuration"] == {"domain": "mg.example.com"}
    assert "api_key" not in saved.json()

    stored = db_session.query(UserCredential).filter_by(user_id=test_user.id).one()
    assert "key-private" not in stored.api_key_encrypted
    assert "mg.example.com" not in stored.config_encrypted

    monkeypatch.setattr(
        "meeting_notes_agent.services.ai_settings_service.AISettingsService._test_provider_connection",
        staticmethod(lambda provider, api_key, config: None),
    )
    tested = client.post(
        "/api/v1/settings/credentials/test",
        headers=auth_headers,
        json={"provider": "mailgun"},
    )
    assert tested.status_code == 200
    assert tested.json()["valid"] is True

    email = client.put(
        "/api/v1/settings/email",
        headers=auth_headers,
        json={
            "email_mode": "byok",
            "provider": "mailgun",
            "sender_name": "Meetings",
            "sender_email": "notes@mg.example.com",
            "reply_to_email": "reply@example.com",
            "smtp_use_tls": True,
        },
    )
    assert email.status_code == 200
    resolved = EmailSettingsService(db_session).resolve_delivery_config(test_user.id)
    assert resolved["provider"] == "mailgun"
    assert resolved["api_key"] == "key-private-mailgun-abcd"
    assert resolved["provider_config"] == {"domain": "mg.example.com"}
    assert resolved["reply_to"] == "reply@example.com"
