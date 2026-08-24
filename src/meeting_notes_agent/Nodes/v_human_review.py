"""Human-in-the-loop review agent for meeting content after redaction."""
from typing import Literal
from langgraph.types import interrupt
from meeting_notes_agent.state_schema import MeetingState


def human_review_agent(state: MeetingState) -> dict:
    """
    Human-in-the-loop agent that presents redacted content for review.

    This node interrupts the graph execution and waits for human feedback.
    The human can:
    - Approve: Proceed to create PM tasks and draft email
    - Reject with instructions: Go back to rewrite (Summarize/Redact)
    - Reject without instructions: Stop the workflow

    Args:
        state (MeetingState): Current state with redacted content

    Returns:
        dict: Contains the human's decision and any rewrite instructions
    """
    # Prepare content for human review
    review_content = {
        "meeting_title": state.meeting_title,
        "meeting_id": state.meeting_id,
        "redacted_transcription": state.redacted_transcription or "",
        "redacted_summary": state.redacted_summary or "",
        "redacted_decisions": state.redacted_decisions or [],
        "redacted_action_items": state.redacted_action_items or [],
    }

    # Interrupt and wait for human input
    human_response = interrupt(
        {
            "type": "human_review",
            # Keep the review fields at the top level. LangGraph Studio and
            # CLI viewers show top-level interrupt values directly, whereas a
            # deeply nested ``content`` field was rendered as an empty label.
            **review_content,
            "prompt": "Review the redacted meeting summary, decisions, and action items before continuing.",
        }
    )

    # Process human response
    decision = human_response.get("decision", "reject_no_instructions").lower()
    instructions = human_response.get("instructions", "").strip()

    if decision == "approve":
        return {
            "human_review_decision": "approve",
            "human_review_instructions": None,
        }
    elif decision == "reject_with_instructions" and instructions:
        return {
            "human_review_decision": "reject_with_instructions",
            "human_review_instructions": instructions,
        }
    else:
        # reject_no_instructions or reject_without_instructions
        return {
            "human_review_decision": "reject_no_instructions",
            "human_review_instructions": None,
        }


def route_after_human_review(state: MeetingState) -> Literal["approve", "reject_with_instructions", "reject_no_instructions"]:
    """
    Conditional edge router based on human review decision.

    Returns the next node to execute based on human's choice.
    """
    decision = state.human_review_decision

    if decision == "approve":
        return "approve"
    elif decision == "reject_with_instructions":
        return "reject_with_instructions"
    else:
        return "reject_no_instructions"


def email_review_agent(state: MeetingState) -> dict:
    """
    Human-in-the-loop agent that presents draft email for review.

    This node interrupts the graph execution and waits for human feedback.
    The human can:
    - Approve: Proceed to send email
    - Reject with instructions: Go back to rewrite email (DraftEmail)
    - Reject without instructions: Stop the workflow

    Args:
        state (MeetingState): Current state with draft email

    Returns:
        dict: Contains the human's decision and any rewrite instructions
    """
    # Prepare content for human review
    review_content = {
        "meeting_title": state.meeting_title,
        "meeting_id": state.meeting_id,
        "email_draft": state.email_draft or "",
        "redacted_summary": state.redacted_summary or "",
        "redacted_decisions": state.redacted_decisions or [],
        "redacted_action_items": state.redacted_action_items or [],
        "email_delivery_error": (
            state.email_response.get("error")
            if isinstance(state.email_response, dict)
            else None
        ),
    }

    # Interrupt and wait for human input
    human_response = interrupt(
        {
            "type": "email_review",
            **review_content,
            "prompt": "Review the draft email and approve it, or request a rewrite before delivery.",
        }
    )

    # Process human response
    decision = human_response.get("decision", "reject_no_instructions").lower()
    instructions = human_response.get("instructions", "").strip()

    if decision == "approve":
        return {
            "email_review_decision": "approve",
            "email_review_instructions": None,
        }
    elif decision == "reject_with_instructions" and instructions:
        return {
            "email_review_decision": "reject_with_instructions",
            "email_review_instructions": instructions,
        }
    else:
        # reject_no_instructions or reject_without_instructions
        return {
            "email_review_decision": "reject_no_instructions",
            "email_review_instructions": None,
        }


def route_after_email_review(state: MeetingState) -> Literal["approve", "reject_with_instructions", "reject_no_instructions"]:
    """
    Conditional edge router based on email review decision.

    Returns the next node to execute based on human's choice.
    """
    decision = state.email_review_decision

    if decision == "approve":
        return "approve"
    elif decision == "reject_with_instructions":
        return "reject_with_instructions"
    else:
        return "reject_no_instructions"
