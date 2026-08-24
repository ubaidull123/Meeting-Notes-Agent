from typing import Any

from meeting_notes_agent.llms.prompts.redaction_prompt import REDACTION
from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.llms.providers import get_chat_llm_for_state
from meeting_notes_agent.utils.retry import llm_retry

@llm_retry
def _invoke_llm_with_retry(state: MeetingState, messages: list) -> Any:
    """Invoke a fresh LLM client with retry logic."""
    return get_chat_llm_for_state(state).invoke(messages)


def _parse_redacted_content(content: str) -> dict:
    """Parse both the required delimiter format and common Markdown headings."""
    values = {
        "redacted_transcription": "",
        "redacted_summary": "",
        "redacted_decisions": [],
        "redacted_action_items": [],
    }
    section_map = {
        "TRANSCRIPTION": "transcription",
        "SUMMARY": "summary",
        "DECISIONS": "decisions",
        "DECISIONS MADE": "decisions",
        "ACTION ITEMS": "action_items",
    }
    current_section = None
    for line in content.split("\n"):
        stripped = line.strip()
        normalized = stripped.strip("= ").lstrip("#").strip().upper()
        if normalized in section_map:
            current_section = section_map[normalized]
            continue
        if not stripped:
            continue
        if current_section == "transcription":
            values["redacted_transcription"] += line + "\n"
        elif current_section == "summary":
            values["redacted_summary"] += line + "\n"
        elif current_section == "decisions" and stripped.startswith("- "):
            values["redacted_decisions"].append(stripped[2:].strip())
        elif current_section == "action_items" and stripped.startswith("- "):
            values["redacted_action_items"].append(stripped[2:].strip())
    values["redacted_transcription"] = values["redacted_transcription"].strip()
    values["redacted_summary"] = values["redacted_summary"].strip()
    values["redacted_decisions"] = [item for item in values["redacted_decisions"] if item and item.lower() != "none"]
    values["redacted_action_items"] = [item for item in values["redacted_action_items"] if item and item.lower() != "none"]
    return values


def redact_sensitive_info(state: MeetingState) -> dict:
    """
    Redacts sensitive information (PII, confidential data) from meeting outputs.

    Args:
        state (MeetingState): The current state containing cleaned transcription,
            summary, decisions, and action items.

    Returns:
        dict: Partial state update with redacted versions of all text fields.
    """
    if state.configuration is not None and not state.configuration.redact_sensitive_information:
        return {
            "redacted_transcription": state.cleaned_transcription or state.raw_transcription or "",
            "redacted_summary": state.summary or "",
            "redacted_decisions": list(state.decisions),
            "redacted_action_items": list(state.action_items),
        }

    # Collect all text content to redact
    content_parts = []

    if state.cleaned_transcription and state.cleaned_transcription.strip():
        content_parts.append(f"=== TRANSCRIPTION ===\n{state.cleaned_transcription}")

    if state.summary and state.summary.strip():
        content_parts.append(f"=== SUMMARY ===\n{state.summary}")

    if state.decisions:
        decisions_text = "\n".join(f"- {d}" for d in state.decisions)
        content_parts.append(f"=== DECISIONS ===\n{decisions_text}")

    if state.action_items:
        actions_text = "\n".join(f"- {a}" for a in state.action_items)
        content_parts.append(f"=== ACTION ITEMS ===\n{actions_text}")

    if not content_parts:
        return {
            "redacted_transcription": "",
            "redacted_summary": "",
            "redacted_decisions": [],
            "redacted_action_items": [],
        }

    full_content = "\n\n".join(content_parts)

    system_prompt = REDACTION
    messages = [
        ("system", system_prompt),
        ("human", full_content),
    ]

    result = _invoke_llm_with_retry(state, messages)
    redacted_content = str(result.content).strip()
    parsed = _parse_redacted_content(redacted_content)

    # Track token usage
    tokens_used = 0
    if hasattr(result, 'usage_metadata') and result.usage_metadata:
        tokens_used = result.usage_metadata.get('total_tokens', 0)
    elif hasattr(result, 'response_metadata') and result.response_metadata:
        tokens_used = result.response_metadata.get('token_usage', {}).get('total_tokens', 0)

    # Providers occasionally return a safe redaction without the requested
    # delimiters. Ask once for repair rather than silently dropping the entire
    # summary and causing a generic email downstream.
    if not any(parsed.values()) and redacted_content:
        repair_messages = [
            ("system", REDACTION + "\n\nYour previous response missed the section headers. Return the redacted content again using the exact headers."),
            ("human", full_content),
        ]
        repaired = _invoke_llm_with_retry(state, repair_messages)
        redacted_content = str(repaired.content).strip()
        parsed = _parse_redacted_content(redacted_content)

        # Track tokens for repair call
        if hasattr(repaired, 'usage_metadata') and repaired.usage_metadata:
            tokens_used += repaired.usage_metadata.get('total_tokens', 0)
        elif hasattr(repaired, 'response_metadata') and repaired.response_metadata:
            tokens_used += repaired.response_metadata.get('token_usage', {}).get('total_tokens', 0)

    # If the model has redacted content but still omitted headers, preserve it
    # as a reviewed summary rather than replacing concrete facts with a generic
    # email. The human-review checkpoint remains before any delivery.
    if not any(parsed.values()) and redacted_content and state.summary:
        parsed["redacted_summary"] = redacted_content

    parsed["tokens_used_accrued"] = state.tokens_used_accrued + tokens_used
    return parsed
