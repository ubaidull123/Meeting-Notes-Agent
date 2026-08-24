"""Cooperative cancellation checks for LangGraph nodes."""
from functools import wraps
from typing import Callable
from uuid import UUID

from meeting_notes_agent.config.core.exceptions import ProcessingCancelled
from meeting_notes_agent.database.models import Meeting, MeetingStatus
from meeting_notes_agent.database.session import SessionLocal
from meeting_notes_agent.state_schema import MeetingState


def ensure_processing_not_cancelled(state: MeetingState) -> None:
    """Raise when the persisted meeting was cancelled by its owner."""
    try:
        meeting_id = UUID(str(state.meeting_id))
    except (TypeError, ValueError):
        return

    db = SessionLocal()
    try:
        status = db.query(Meeting.status).filter(Meeting.id == meeting_id).scalar()
        if status == MeetingStatus.CANCELLED:
            raise ProcessingCancelled("Meeting processing was stopped by the user")
    finally:
        db.close()


def cancellable_node(node: Callable) -> Callable:
    """Check persisted cancellation immediately before and after a graph node."""
    @wraps(node)
    def wrapped(state: MeetingState):
        ensure_processing_not_cancelled(state)
        result = node(state)
        ensure_processing_not_cancelled(state)
        return result

    return wrapped
