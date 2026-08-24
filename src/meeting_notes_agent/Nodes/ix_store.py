"""Final graph storage acknowledgement.

The API service persists meeting state and bills usage in one SQLAlchemy
transaction after the graph completes.  Keeping this node side-effect free
prevents duplicate charges when LangGraph resumes a review checkpoint.
"""
from typing import Any
from meeting_notes_agent.state_schema import MeetingState


def store_meeting(state: MeetingState) -> dict[str, Any]:
    """
    Mark the workflow storage step complete.

    Args:
        state (MeetingState): Current state containing all meeting data.

    Returns:
        dict: Partial state update with storage status.
    """
    return {"stored": True, "storage_error": None}
