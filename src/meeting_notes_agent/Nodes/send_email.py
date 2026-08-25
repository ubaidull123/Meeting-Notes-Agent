"""Send email node for the meeting notes agent graph."""
from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.database import SessionLocal
from meeting_notes_agent.database.models import Meeting, MeetingEmailRecipient, Task
from meeting_notes_agent.config.core.config import settings
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
    if not (state.redacted_summary or state.redacted_decisions or state.redacted_action_items):
        return {
            "email_sent": False,
            "email_response": {
                "status": "not_sent",
                "error": "Email not sent because no verified redacted meeting content is available. Request a summary rewrite first.",
                "retryable": False,
            },
        }

    email_config = _email_config_for_state(state)
    meeting_url = f"{settings.frontend_app_url.rstrip('/')}/meetings/{state.meeting_id}"
    db = SessionLocal() if state.user_id is not None else None
    try:
        meeting_id = UUID(str(state.meeting_id))
        recipients = (
            db.query(MeetingEmailRecipient)
            .filter(MeetingEmailRecipient.meeting_id == meeting_id)
            .order_by(MeetingEmailRecipient.selected_at.asc())
            .all()
            if db is not None
            else []
        )
        if recipients:
            deliveries: list[dict[str, Any]] = []
            for recipient in recipients:
                if recipient.status == "sent":
                    deliveries.append(
                        {"user_id": recipient.user_id, "email": recipient.email, "status": "sent"}
                    )
                    continue
                task_titles = [
                    title
                    for title, in db.query(Task.title)
                    .filter(
                        Task.meeting_id == meeting_id,
                        Task.assigned_user_id == recipient.user_id,
                    )
                    .order_by(Task.created_at.asc())
                    .all()
                ]
                try:
                    response = send_meeting_summary_email(
                        to=[recipient.email],
                        meeting_title=state.meeting_title or "Meeting Summary",
                        summary=state.email_draft or state.redacted_summary or state.summary or "No summary available",
                        decisions=[] if state.email_draft else (state.redacted_decisions or state.decisions or []),
                        action_items=task_titles,
                        from_email=email_config.get("from_email"),
                        provider_override=email_config.get("provider"),
                        api_key_override=email_config.get("api_key"),
                        provider_config=email_config.get("provider_config"),
                        reply_to=email_config.get("reply_to"),
                        meeting_url=meeting_url,
                    )
                    recipient.status = "sent"
                    recipient.sent_at = datetime.now(timezone.utc)
                    recipient.delivery_error = None
                    recipient.delivery_response = response
                    db.commit()
                    deliveries.append(
                        {"user_id": recipient.user_id, "email": recipient.email, "status": "sent"}
                    )
                except EmailDeliveryError as exc:
                    recipient.status = "failed"
                    recipient.delivery_error = str(exc)
                    recipient.delivery_response = {
                        "status": "failed",
                        "error": str(exc),
                        "attempts": exc.attempts,
                        "retryable": exc.retryable,
                    }
                    db.commit()
                    deliveries.append(
                        {"user_id": recipient.user_id, "email": recipient.email, "status": "failed", "error": str(exc)}
                    )
            failed = [item for item in deliveries if item["status"] != "sent"]
            return {
                "email_sent": not failed,
                "email_response": {
                    "status": "sent" if not failed else "partial_failure",
                    "deliveries": deliveries,
                    "error": "One or more selected recipients could not be reached" if failed else None,
                },
            }

        persisted_meeting = db.get(Meeting, meeting_id) if db is not None else None
        if persisted_meeting is not None and persisted_meeting.restrict_to_participants:
            return {
                "email_sent": False,
                "email_response": {
                    "status": "not_sent",
                    "error": "No meeting-specific email recipients were selected.",
                    "retryable": False,
                },
            }

        # Compatibility path for legacy meetings that predate structured
        # participants and recipient selection.
        to_emails = [attendee.email for attendee in state.attendees if attendee.email]
        if not to_emails:
            return {
                "email_sent": False,
                "email_response": {"status": "not_sent", "error": "No recipient emails found in attendees", "retryable": False},
            }
        try:
            response = send_meeting_summary_email(
                to=to_emails,
                meeting_title=state.meeting_title or "Meeting Summary",
                summary=state.email_draft or state.redacted_summary or state.summary or "No summary available",
                decisions=[] if state.email_draft else (state.redacted_decisions or state.decisions or []),
                action_items=[] if state.email_draft else (state.redacted_action_items or state.action_items or []),
                from_email=email_config.get("from_email"),
                provider_override=email_config.get("provider"),
                api_key_override=email_config.get("api_key"),
                provider_config=email_config.get("provider_config"),
                reply_to=email_config.get("reply_to"),
                meeting_url=meeting_url,
            )
            return {"email_sent": True, "email_response": response}
        except EmailDeliveryError as exc:
            return {
                "email_sent": False,
                "email_response": {"status": "failed", "error": str(exc), "attempts": exc.attempts, "retryable": exc.retryable},
            }
    finally:
        if db is not None:
            db.close()


def route_after_send_email(state: MeetingState) -> str:
    """Return to email review when delivery fails so the error stays actionable."""
    return "sent" if state.email_sent else "failed"
