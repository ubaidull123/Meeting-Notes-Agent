from src.state_schema import MeetingState
from src.llms.API_Based.openai import get_openai_llm

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

    system_prompt = (
        "You are a data privacy specialist. Redact sensitive information from the "
        "provided meeting content while preserving the overall meaning and structure.\n\n"
        "REDACT the following types of information (replace with [REDACTED]):\n"
        "1. Person names (first, last, full names)\n"
        "2. Email addresses\n"
        "3. Phone numbers (including extensions)\n"
        "4. Physical addresses (street, city, state, zip, country)\n"
        "4. Financial data: credit card numbers, bank account numbers, routing numbers\n"
        "5. Government IDs: SSN, passport numbers, driver's license numbers, tax IDs\n"
        "6. Authentication credentials: passwords, API keys, tokens, secrets\n"
        "7. Confidential project codenames or internal references\n"
        "8. Medical/health information (HIPAA)\n"
        "9. Legal case numbers or privileged information\n"
        "10. IP addresses and MAC addresses\n\n"
        "PRESERVE:\n"
        "- General business terms, department names, public project names\n"
        "- Dates, times, durations (unless tied to specific sensitive events)\n"
        "- Monetary amounts without account context\n"
        "- Action items, decisions, and summary structure\n\n"
        "Return the redacted content in the SAME format with the same section headers. "
        "Each section should start with its header (e.g., '=== TRANSCRIPTION ===')."
    )

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