import re
from typing import Any

from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.llms.providers import get_chat_llm_for_state
from meeting_notes_agent.utils.retry import llm_retry


@llm_retry
def _invoke_llm_with_retry(state: MeetingState, messages: list) -> Any:
    """Invoke a fresh LLM client with retry logic."""
    return get_chat_llm_for_state(state).invoke(messages)


def draft_email(state: MeetingState) -> dict:
    """
    Drafts an email based on the meeting context.
    Supports rewrite instructions from email review.

    Args:
        state (MeetingState): Current state containing meeting data
            and optional email_review_instructions for rewriting.

    Returns:
        dict: Partial state update with email_draft.
    """
    summary = state.redacted_summary or ""
    decisions = state.redacted_decisions or []
    action_items = state.redacted_action_items or []

    # Check if we have rewrite instructions from email review
    rewrite_instructions = state.email_review_instructions

    if not summary.strip() and not decisions and not action_items:
        return {
            "email_draft": "No verified redacted meeting content is available. Request a summary rewrite before sending an email.",
            "email_review_instructions": None,
            "email_review_decision": None,
        }

    if rewrite_instructions:
        # Rewrite mode: incorporate human instructions
        system_prompt = (
            "You are a professional email drafter. Draft a clear, concise, and professional "
            "email based on the meeting context and user instructions. Use the meeting details "
            "to create a well-structured email that covers the key points.\n\n"
            "IMPORTANT: You are rewriting the email based on human feedback.\n"
            f"Human Instructions: {rewrite_instructions}\n"
            "Please regenerate the email incorporating these instructions. Do not use Markdown headings or "
            "mention speaker labels."
        )
    else:
        # Normal mode
        system_prompt = (
            "You are a professional email drafter. Draft a clear, concise, and professional "
            "email based on the meeting context. Start with a friendly greeting, use two short plain-text "
            "paragraphs, then concise labelled lists for decisions and action items, and end with a closing. "
            "Use only concrete facts present in the supplied summary, decisions, and action items. Never invent a project, "
            "decision, action item, or outcome. Do not write generic filler such as 'valuable discussion', 'feel free to share "
            "additional thoughts', or 'as we move forward'. Do not use Markdown headings, hash characters, asterisks, or generic Speaker labels."
        )

    user_prompt = f"""
Meeting Title: {state.meeting_title}

Summary:
{summary}

Decisions Made:
{chr(10).join(f"- {d}" for d in decisions) if decisions else "None"}

Action Items:
{chr(10).join(f"- {a}" for a in action_items) if action_items else "None"}

Write only the email body. Do not preface it with an explanation.
"""

    messages = [
        ("system", system_prompt),
        ("human", user_prompt),
    ]

    result = _invoke_llm_with_retry(state, messages)
    email_draft = result.content if hasattr(result, 'content') else str(result)
    email_draft = re.sub(r"(?m)^#{1,6}\s*", "", str(email_draft))
    email_draft = email_draft.replace("**", "").replace("__", "")
    email_draft = re.sub(r"(?i)\bspeaker\s+\d+\s*:\s*", "", email_draft)
    email_draft = re.sub(r"\n{3,}", "\n\n", email_draft).strip()

    # Track token usage
    tokens_used = 0
    if hasattr(result, 'usage_metadata') and result.usage_metadata:
        tokens_used = result.usage_metadata.get('total_tokens', 0)
    elif hasattr(result, 'response_metadata') and result.response_metadata:
        tokens_used = result.response_metadata.get('token_usage', {}).get('total_tokens', 0)

    # Clear the email review instructions after using them
    return {
        "email_draft": email_draft,
        "email_review_instructions": None,
        "email_review_decision": None,
        "tokens_used_accrued": state.tokens_used_accrued + tokens_used,
    }
