import os
import sqlite3
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from meeting_notes_agent.observability import configure_langsmith
from meeting_notes_agent.Nodes.iv_summerize import summarize_meeting_notes
from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.Nodes.i_Input import get_input_node, check_quota
from meeting_notes_agent.Nodes.ii_transcribe_audio import transcribe_audio
from meeting_notes_agent.Nodes.iii_clean_transcript import clean_transcript
from meeting_notes_agent.Nodes.vi_redaction import redact_sensitive_info
from meeting_notes_agent.Nodes.vii_PM_tasks import create_pm_tasks
from meeting_notes_agent.Nodes.viii_emailing import draft_email
from meeting_notes_agent.Nodes.send_email import send_email_node, route_after_send_email
from meeting_notes_agent.Nodes.ix_store import store_meeting
from meeting_notes_agent.Nodes.v_human_review import human_review_agent, route_after_human_review, email_review_agent, route_after_email_review
from meeting_notes_agent.database.postgresdb import get_checkpointer
from meeting_notes_agent.config.core.config import settings
from meeting_notes_agent.utils.cancellation import cancellable_node

configure_langsmith()

_graph = None
_sqlite_checkpoint_connection = None


def route_after_redaction(state: MeetingState) -> str:
    configuration = state.configuration
    return "review" if configuration is None or configuration.require_human_review else "continue"


def route_after_tasks(state: MeetingState) -> str:
    configuration = state.configuration
    return "draft_email" if configuration is None or configuration.generate_follow_up_email else "store"


def route_after_email_draft(state: MeetingState) -> str:
    configuration = state.configuration
    return "review" if configuration is None or configuration.require_email_approval else "send"


def _get_sqlite_checkpointer() -> SqliteSaver:
    """Return a process-wide saver backed by a durable local SQLite file."""
    global _sqlite_checkpoint_connection
    if _sqlite_checkpoint_connection is None:
        checkpoint_path = Path(settings.langgraph_checkpoint_db)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        _sqlite_checkpoint_connection = sqlite3.connect(
            checkpoint_path,
            check_same_thread=False,
        )
    serializer = JsonPlusSerializer(
        allowed_msgpack_modules=[("meeting_notes_agent.state_schema", "Attendee")],
    )
    return SqliteSaver(_sqlite_checkpoint_connection, serde=serializer)


def build_graph() -> StateGraph:
    """Build and return the meeting notes agent graph with human-in-the-loop reviews."""
    global _graph
    if _graph is not None:
        return _graph

    graph = StateGraph(MeetingState)

    graph.add_node("Input", cancellable_node(get_input_node))
    graph.add_node("CheckQuota", cancellable_node(check_quota))
    graph.add_node("TranscribeAudio", cancellable_node(transcribe_audio))
    graph.add_node("CleanTranscript", cancellable_node(clean_transcript))
    graph.add_node("Summarize", cancellable_node(summarize_meeting_notes))
    graph.add_node("RedactSensitiveInfo", cancellable_node(redact_sensitive_info))
    graph.add_node("HumanReview", cancellable_node(human_review_agent))
    graph.add_node("CreatePMTasks", cancellable_node(create_pm_tasks))
    graph.add_node("DraftEmail", cancellable_node(draft_email))
    graph.add_node("EmailReview", cancellable_node(email_review_agent))
    graph.add_node("SendEmail", cancellable_node(send_email_node))
    graph.add_node("StoreMeeting", cancellable_node(store_meeting))

    graph.add_edge(START, "Input")
    graph.add_edge("Input", "CheckQuota")
    graph.add_edge("CheckQuota", "TranscribeAudio")
    graph.add_edge("TranscribeAudio", "CleanTranscript")
    graph.add_edge("CleanTranscript", "Summarize")
    graph.add_edge("Summarize", "RedactSensitiveInfo")
    graph.add_conditional_edges(
        "RedactSensitiveInfo",
        route_after_redaction,
        {"review": "HumanReview", "continue": "CreatePMTasks"},
    )

    # Conditional routing after first human review (after redaction)
    graph.add_conditional_edges(
        "HumanReview",
        route_after_human_review,
        {
            "approve": "CreatePMTasks",
            "reject_with_instructions": "Summarize",
            "reject_no_instructions": END,
        },
    )

    graph.add_conditional_edges(
        "CreatePMTasks",
        route_after_tasks,
        {"draft_email": "DraftEmail", "store": "StoreMeeting"},
    )
    graph.add_conditional_edges(
        "DraftEmail",
        route_after_email_draft,
        {"review": "EmailReview", "send": "SendEmail"},
    )

    # Conditional routing after second human review (after draft email)
    graph.add_conditional_edges(
        "EmailReview",
        route_after_email_review,
        {
            "approve": "SendEmail",
            "reject_with_instructions": "DraftEmail",
            "reject_no_instructions": END,
        },
    )

    graph.add_conditional_edges(
        "SendEmail",
        route_after_send_email,
        {
            "sent": "StoreMeeting",
            "failed": "EmailReview",
        },
    )
    graph.add_edge("StoreMeeting", END)


    if os.environ.get("LANGGRAPH_API_URL") or os.environ.get("LANGGRAPH_DEV"):
        return graph.compile()

    if settings.database_url.startswith("sqlite"):
        return graph.compile(checkpointer=_get_sqlite_checkpointer())

    checkpointer = get_checkpointer()
    checkpointer.setup()
    return graph.compile(checkpointer=checkpointer)  # type: ignore


graph = build_graph()


if __name__ == "__main__":
    print("Graph compiled successfully")
    print("Nodes:", list(graph.get_graph().nodes.keys())) # type: ignore
