"""Send email node for the meeting notes agent graph."""
from typing import Any
from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.database import SessionLocal
from meeting_notes_agent.services.email_settings_service import EmailSettingsService
from meeting_notes_agent.utils.email_utils import EmailDeliveryError, send_meeting_summary_email


def _email_config_for_state(state: MeetingState) -> dict:
    if state.user_id is None:
        return {}
    db = SessionLocal()
    try:
        return EmailSettingsService(db).resolve_delivery_config(state.user_id)
    finally:
        db.close()


def send_email_node(state: MeetingState) -> dict[str, Any]:
    """
    Send meeting summary email to attendees.

    Args:
        state (MeetingState): Current state containing meeting data and email_draft.

    Returns:
        dict: Partial state update with email_sent status and email_response.
    """
    # Get recipient emails from attendees
    to_emails = [attendee.email for attendee in state.attendees if attendee.email]

    if not to_emails:
        return {
            "email_sent": False,
            "email_response": {"status": "not_sent", "error": "No recipient emails found in attendees", "retryable": False},
        }

    # Use email_draft if available, otherwise build from meeting data
    if not (state.redacted_summary or state.redacted_decisions or state.redacted_action_items):
        return {
            "email_sent": False,
            "email_response": {
                "status": "not_sent",
                "error": "Email not sent because no verified redacted meeting content is available. Request a summary rewrite first.",
                "retryable": False,
            },
        }

    if state.email_draft:
        # Send the drafted email as HTML
        try:
            email_config = _email_config_for_state(state)
            response = send_meeting_summary_email(
                to=to_emails,
                meeting_title=state.meeting_title or "Meeting Summary",
                summary=state.email_draft,
                decisions=[],  # Already included in email_draft
                action_items=[],  # Already included in email_draft
                from_email=email_config.get("from_email"),
                provider_override=email_config.get("provider"),
                api_key_override=email_config.get("api_key"),
                provider_config=email_config.get("provider_config"),
                reply_to=email_config.get("reply_to"),
            )
            return {
                "email_sent": True,
                "email_response": response,
            }
        except EmailDeliveryError as exc:
            return {
                "email_sent": False,
                "email_response": {"status": "failed", "error": str(exc), "attempts": exc.attempts, "retryable": exc.retryable},
            }

    try:
        email_config = _email_config_for_state(state)
        response = send_meeting_summary_email(
            to=to_emails,
            meeting_title=state.meeting_title or "Meeting Summary",
            summary=state.redacted_summary or state.summary or "No summary available",
            decisions=state.redacted_decisions or state.decisions or [],
            action_items=state.redacted_action_items or state.action_items or [],
            from_email=email_config.get("from_email"),
            provider_override=email_config.get("provider"),
            api_key_override=email_config.get("api_key"),
            provider_config=email_config.get("provider_config"),
            reply_to=email_config.get("reply_to"),
        )
        return {
            "email_sent": True,
            "email_response": response,
        }
    except EmailDeliveryError as exc:
        return {
            "email_sent": False,
            "email_response": {"status": "failed", "error": str(exc), "attempts": exc.attempts, "retryable": exc.retryable},
        }


def route_after_send_email(state: MeetingState) -> str:
    """Return to email review when delivery fails so the error stays actionable."""
    return "sent" if state.email_sent else "failed"
