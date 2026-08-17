from src.state_schema import MeetingState
from src.llms.API_Based.openai import get_openai_llm

llm = get_openai_llm()


def summarize_meeting_notes(state: MeetingState) -> dict:
    """
    Summarizes the meeting notes using an LLM with structured output.

    Args:
        state (MeetingState): The current state containing cleaned transcription.

    Returns:
        dict: Partial state update with summary, decisions, and action_items.
    """
    transcript = state.cleaned_transcription or ""
    if not transcript.strip():
        return {"summary": "", "decisions": [], "action_items": []}

    system_prompt = (
        "You are a meeting notes summarizer. Given a cleaned meeting transcript, "
        "produce a structured summary with the following sections:\n\n"
        "## Summary\n"
        "A concise paragraph (3-5 sentences) capturing the meeting's purpose, "
        "key discussion points, and outcomes.\n\n"
        "## Decisions Made\n"
        "Explicit decisions reached during the meeting. Each on a new line prefixed with '- '.\n"
        "If no decisions were made, write 'None'.\n\n"
        "## Action Items\n"
        "Specific tasks assigned with owner and due date if mentioned. "
        "Each on a new line prefixed with '- '. If none, write 'None'.\n\n"
        "Return ONLY the structured summary with these three sections, nothing else."
    )

    messages = [
        ("system", system_prompt),
        ("human", transcript),
    ]

    result = llm.invoke(messages)
    content = str(result.content).strip()

    summary = ""
    decisions = []
    action_items = []

    current_section = None
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("## Summary"):
            current_section = "summary"
            continue
        elif line.startswith("## Decisions Made"):
            current_section = "decisions"
            continue
        elif line.startswith("## Action Items"):
            current_section = "action_items"
            continue
        elif not line:
            continue

        if current_section == "summary":
            summary += line + " "
        elif current_section == "decisions" and line.startswith("- "):
            decision = line[2:].strip()
            if decision.lower() != "none":
                decisions.append(decision)
        elif current_section == "action_items" and line.startswith("- "):
            action = line[2:].strip()
            if action.lower() != "none":
                action_items.append(action)

    if not summary.strip():
        summary = content

    return {
        "summary": summary.strip(),
        "decisions": decisions,
        "action_items": action_items,
    }


# Backward compatibility alias
summerize_meeting_notes = summarize_meeting_notes