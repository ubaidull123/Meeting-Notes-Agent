"""Email configuration and delivery-routing regression tests."""
from datetime import date
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from meeting_notes_agent.Nodes.send_email import route_after_send_email, send_email_node
from meeting_notes_agent.auth.security import hash_password
from meeting_notes_agent.database.models import (
    Attendee as DatabaseAttendee,
    Meeting,
    MeetingEmailRecipient,
    Task,
    TaskPriority,
    TaskStatus,
    TeamMembership,
    TeamRole,
    User,
)
from meeting_notes_agent.state_schema import Attendee, MeetingState
from meeting_notes_agent.utils.email_utils import EmailDeliveryError, send_email


def test_resend_configuration_is_loaded_for_each_send(monkeypatch):
    sent_keys = []

    def fake_send(params):
        import resend

        sent_keys.append(resend.api_key)
        return {"id": "email-id"}

    monkeypatch.setattr("resend.Emails.send", fake_send)
    monkeypatch.setenv("RESEND_FROM_EMAIL", "Meeting Notes <notes@verified.example>")

    monkeypatch.setenv("RESEND_API_KEY", "first-key")
    send_email(["person@example.com"], "Subject", "<p>Body</p>")
    monkeypatch.setenv("RESEND_API_KEY", "rotated-key")
    send_email(["person@example.com"], "Subject", "<p>Body</p>")

    assert sent_keys == ["first-key", "rotated-key"]


def test_onboarding_domain_rejects_arbitrary_attendees_before_api_call(monkeypatch):
    provider_send = Mock()
    monkeypatch.setattr("resend.Emails.send", provider_send)
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "Meeting Notes <onboarding@resend.dev>")
    monkeypatch.setenv("RESEND_TEST_RECIPIENT", "owner@example.com")

    with pytest.raises(EmailDeliveryError, match="testing-only") as exc_info:
        send_email(["attendee@example.com"], "Subject", "<p>Body</p>")

    assert exc_info.value.attempts == 0
    assert exc_info.value.retryable is False
    provider_send.assert_not_called()


def test_send_failure_routes_back_to_email_review(monkeypatch):
    def fail_send(**kwargs):
        raise EmailDeliveryError("Verify a sender domain", attempts=0, retryable=False)

    monkeypatch.setattr(
        "meeting_notes_agent.Nodes.send_email.send_meeting_summary_email",
        fail_send,
    )
    state = MeetingState(
        meeting_title="Delivery test",
        transcript_text="Transcript",
        attendees=[Attendee(name="Reviewer", email="reviewer@example.com")],
        redacted_summary="Reviewed summary",
        email_draft="Reviewed email",
    )

    result = send_email_node(state)
    resumed_state = state.model_copy(update=result)

    assert result["email_sent"] is False
    assert result["email_response"]["error"] == "Verify a sender domain"
    assert route_after_send_email(resumed_state) == "failed"


def test_only_selected_participant_receives_personalized_follow_up(
    db_session, test_user, monkeypatch
):
    teammate = User(
        email=f"unselected-{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("EmailRecipientPass123!"),
        full_name="Unselected Participant",
    )
    db_session.add(teammate)
    db_session.flush()
    team_id = test_user.team_memberships[0].team_id
    db_session.add(
        TeamMembership(team_id=team_id, user_id=teammate.id, role=TeamRole.MEMBER)
    )
    meeting = Meeting(
        user_id=test_user.id,
        team_id=team_id,
        created_by=test_user.id,
        title="Selected delivery",
        meeting_date=date.today(),
        transcript_text="Transcript",
        redacted_summary="Reviewed summary",
        restrict_to_participants=True,
    )
    db_session.add(meeting)
    db_session.flush()
    selected = DatabaseAttendee(
        meeting_id=meeting.id,
        user_id=test_user.id,
        name=test_user.full_name,
        email=test_user.email,
    )
    unselected = DatabaseAttendee(
        meeting_id=meeting.id,
        user_id=teammate.id,
        name=teammate.full_name,
        email=teammate.email,
    )
    db_session.add_all([selected, unselected])
    db_session.flush()
    db_session.add_all(
        [
            MeetingEmailRecipient(
                meeting_id=meeting.id,
                attendee_id=selected.id,
                user_id=test_user.id,
                email=test_user.email,
                status="pending",
                selected_by=test_user.id,
            ),
            Task(
                id=uuid4().hex[:8],
                meeting_id=meeting.id,
                team_id=team_id,
                assigned_user_id=test_user.id,
                meeting_title=meeting.title,
                title="Implement secure meeting links",
                status=TaskStatus.TODO,
                priority=TaskPriority.HIGH,
                action_item_index=0,
            ),
        ]
    )
    db_session.commit()

    captured = []

    def capture_send(**kwargs):
        captured.append(kwargs)
        return {"id": "selected-only"}

    LocalSession = sessionmaker(bind=db_session.bind)
    monkeypatch.setattr("meeting_notes_agent.Nodes.send_email.SessionLocal", LocalSession)
    monkeypatch.setattr(
        "meeting_notes_agent.Nodes.send_email._email_config_for_state", lambda state: {}
    )
    monkeypatch.setattr(
        "meeting_notes_agent.Nodes.send_email.send_meeting_summary_email", capture_send
    )

    result = send_email_node(
        MeetingState(
            meeting_id=str(meeting.id),
            user_id=test_user.id,
            meeting_title=meeting.title,
            transcript_text="Transcript",
            attendees=[
                Attendee(name=test_user.full_name, email=test_user.email),
                Attendee(name=teammate.full_name, email=teammate.email),
            ],
            redacted_summary="Reviewed summary",
            email_draft="Reviewed follow-up",
        )
    )

    assert result["email_sent"] is True
    assert len(captured) == 1
    assert captured[0]["to"] == [test_user.email]
    assert teammate.email not in captured[0]["to"]
    assert captured[0]["action_items"] == ["Implement secure meeting links"]
    assert captured[0]["meeting_url"].endswith(f"/meetings/{meeting.id}")
    db_session.expire_all()
    audit = db_session.query(MeetingEmailRecipient).filter_by(meeting_id=meeting.id).one()
    assert audit.status == "sent"
    assert audit.sent_at is not None


def test_structured_meeting_without_selected_recipients_sends_nothing(
    db_session, test_user, monkeypatch
):
    team_id = test_user.team_memberships[0].team_id
    meeting = Meeting(
        user_id=test_user.id,
        team_id=team_id,
        created_by=test_user.id,
        title="Recipient selection required",
        meeting_date=date.today(),
        transcript_text="Transcript",
        redacted_summary="Reviewed summary",
        restrict_to_participants=True,
    )
    db_session.add(meeting)
    db_session.flush()
    db_session.add(
        DatabaseAttendee(
            meeting_id=meeting.id,
            user_id=test_user.id,
            name=test_user.full_name,
            email=test_user.email,
        )
    )
    db_session.commit()

    captured = []
    LocalSession = sessionmaker(bind=db_session.bind)
    monkeypatch.setattr("meeting_notes_agent.Nodes.send_email.SessionLocal", LocalSession)
    monkeypatch.setattr(
        "meeting_notes_agent.Nodes.send_email._email_config_for_state", lambda state: {}
    )
    monkeypatch.setattr(
        "meeting_notes_agent.Nodes.send_email.send_meeting_summary_email",
        lambda **kwargs: captured.append(kwargs),
    )

    result = send_email_node(
        MeetingState(
            meeting_id=str(meeting.id),
            user_id=test_user.id,
            meeting_title=meeting.title,
            transcript_text="Transcript",
            attendees=[Attendee(name=test_user.full_name, email=test_user.email)],
            redacted_summary="Reviewed summary",
            email_draft="Reviewed follow-up",
        )
    )

    assert result["email_sent"] is False
    assert result["email_response"]["status"] == "not_sent"
    assert "selected" in result["email_response"]["error"]
    assert captured == []
