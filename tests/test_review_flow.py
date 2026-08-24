"""Tests for persisted human-review checkpoints and review decisions."""
from datetime import date
import sqlite3
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from meeting_notes_agent.database.models import Attendee, Meeting, MeetingStatus
from meeting_notes_agent.config.core.exceptions import ProcessingCancelled
from meeting_notes_agent.schemas.meeting import ReviewRequest
from meeting_notes_agent.services.processing_service import ProcessingService
from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.utils.cancellation import ensure_processing_not_cancelled


class ReviewGraph:
    """Small deterministic graph replacement; no network or LLM calls."""

    def __init__(self):
        self.values = {
            "raw_transcription": "Raw transcript",
            "cleaned_transcription": "Clean transcript",
            "summary": "Generated summary",
            "decisions": ["Use Groq"],
            "action_items": ["Review the notes"],
            "redacted_summary": "Redacted summary",
            "redacted_decisions": ["Use Groq"],
            "redacted_action_items": ["Review the notes"],
            "tokens_used_accrued": 42,
        }

    def invoke(self, payload, config):
        if payload.__class__.__name__ == "Command":
            return dict(self.values)
        return {"__interrupt__": [SimpleNamespace(value={"type": "human_review"})]}

    def get_state(self, config):
        return SimpleNamespace(values=self.values, next=("HumanReview",))


def test_human_review_persists_checkpoint_and_rejects_cleanly(db_session, test_user):
    meeting = Meeting(
        id=uuid4(),
        user_id=test_user.id,
        title="Review flow",
        meeting_date=date.today(),
        transcript_text="A valid input transcript.",
        status=MeetingStatus.DRAFT,
    )
    db_session.add(meeting)
    db_session.add(Attendee(meeting_id=meeting.id, name="Reviewer", email="reviewer@example.com"))
    db_session.commit()

    service = ProcessingService(db_session)
    service._graph = ReviewGraph()

    service.start_processing(meeting.id, test_user.id)
    db_session.refresh(meeting)
    assert meeting.status == MeetingStatus.AWAITING_REVIEW
    assert meeting.redacted_summary == "Redacted summary"

    content = service.get_review_content(meeting.id, test_user.id)
    assert content.redacted_summary == "Redacted summary"
    assert content.redacted_action_items == ["Review the notes"]

    response = service.resume_processing(meeting.id, test_user.id, ReviewRequest(decision="reject"))
    db_session.refresh(meeting)
    assert response.next_status == "rejected"
    assert meeting.status == MeetingStatus.REJECTED
    assert meeting.error_message is None


def test_queue_processing_returns_before_graph_execution(db_session, test_user):
    meeting = Meeting(
        id=uuid4(),
        user_id=test_user.id,
        title="Queued flow",
        meeting_date=date.today(),
        transcript_text="A valid input transcript.",
        status=MeetingStatus.DRAFT,
    )
    db_session.add(meeting)
    db_session.add(Attendee(meeting_id=meeting.id, name="Reviewer", email="reviewer@example.com"))
    db_session.commit()

    service = ProcessingService(db_session)
    response = service.queue_processing(meeting.id, test_user.id)

    db_session.refresh(meeting)
    assert response.status == "queued"
    assert response.thread_id == meeting.thread_id
    assert meeting.status == MeetingStatus.QUEUED


def test_real_checkpoint_resume_survives_process_restart(tmp_path):
    """Regression: built-in interrupt state must survive an API reload."""
    def review_node(state: MeetingState) -> dict:
        response = interrupt({"type": "human_review"})
        return {"human_review_decision": response["decision"]}

    def compile_graph(connection):
        builder = StateGraph(MeetingState)
        builder.add_node("Review", review_node)
        builder.add_edge(START, "Review")
        builder.add_edge("Review", END)
        return builder.compile(checkpointer=SqliteSaver(connection))

    checkpoint_path = tmp_path / "approval-checkpoints.sqlite"
    config = {"configurable": {"thread_id": str(uuid4())}}
    state = MeetingState(
        meeting_title="Resume regression",
        transcript_text="A valid transcript.",
    )

    first_connection = sqlite3.connect(checkpoint_path, check_same_thread=False)
    first_graph = compile_graph(first_connection)
    first = first_graph.invoke(state.model_dump(), config=config)
    assert "__interrupt__" in first
    first_connection.close()

    second_connection = sqlite3.connect(checkpoint_path, check_same_thread=False)
    second_graph = compile_graph(second_connection)
    resumed = second_graph.invoke(Command(resume={"decision": "approve"}), config=config)
    assert resumed["human_review_decision"] == "approve"
    second_connection.close()


def test_cancelled_meeting_stops_graph_nodes(db_session, test_user):
    meeting = Meeting(
        id=uuid4(),
        user_id=test_user.id,
        title="Cancellation flow",
        meeting_date=date.today(),
        transcript_text="A valid input transcript.",
        status=MeetingStatus.PROCESSING,
    )
    db_session.add(meeting)
    db_session.add(Attendee(meeting_id=meeting.id, name="Reviewer", email="reviewer@example.com"))
    db_session.commit()

    response = ProcessingService(db_session).cancel_processing(meeting.id, test_user.id)
    assert response.status == "cancelled"

    state = MeetingState(
        meeting_id=str(meeting.id),
        user_id=test_user.id,
        meeting_title=meeting.title,
        transcript_text=meeting.transcript_text,
    )
    with pytest.raises(ProcessingCancelled):
        ensure_processing_not_cancelled(state)
