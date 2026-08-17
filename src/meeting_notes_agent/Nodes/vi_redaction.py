from meeting_notes_agent.llms.prompts.redaction_prompt import REDACTION
from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.llms.API_Based.openai import get_openai_llm

llm = get_openai_llm()


def redact_sensitive_info(state: MeetingState) -> dict:
    """
    Redacts sensitive information (PII, confidential data) from meeting outputs.

    Args:
        state (MeetingState): The current state containing cleaned transcription,
            summary, decisions, and action items.

    Returns:
        dict: Partial state update with redacted versions of all text fields.
    """
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

    result = llm.invoke(messages)
    redacted_content = str(result.content).strip()

    # Parse the redacted sections
    redacted_transcription = ""
    redacted_summary = ""
    redacted_decisions = []
    redacted_action_items = []

    current_section = None
    for line in redacted_content.split("\n"):
        line_stripped = line.strip()

        if line_stripped.startswith("=== TRANSCRIPTION ==="):
            current_section = "transcription"
            continue
        elif line_stripped.startswith("=== SUMMARY ==="):
            current_section = "summary"
            continue
        elif line_stripped.startswith("=== DECISIONS ==="):
            current_section = "decisions"
            continue
        elif line_stripped.startswith("=== ACTION ITEMS ==="):
            current_section = "action_items"
            continue

        if not line_stripped:
            continue

        if current_section == "transcription":
            redacted_transcription += line + "\n"
        elif current_section == "summary":
            redacted_summary += line + "\n"
        elif current_section == "decisions" and line_stripped.startswith("- "):
            decision = line_stripped[2:].strip()
            if decision and decision.lower() != "none":
                redacted_decisions.append(decision)
        elif current_section == "action_items" and line_stripped.startswith("- "):
            action = line_stripped[2:].strip()
            if action and action.lower() != "none":
                redacted_action_items.append(action)

    return {
        "redacted_transcription": redacted_transcription.strip(),
        "redacted_summary": redacted_summary.strip(),
        "redacted_decisions": redacted_decisions,
        "redacted_action_items": redacted_action_items,
    }