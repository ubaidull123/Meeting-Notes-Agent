"""Email configuration and delivery-routing regression tests."""
from unittest.mock import Mock

import pytest

from meeting_notes_agent.Nodes.send_email import route_after_send_email, send_email_node
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
