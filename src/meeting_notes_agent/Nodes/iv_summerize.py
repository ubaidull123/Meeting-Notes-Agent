from typing import Any

from meeting_notes_agent.llms.prompts.summarize_prompt import SUMMRIZE
from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.llms.providers import get_chat_llm_for_state
from meeting_notes_agent.utils.retry import llm_retry


@llm_retry
def _invoke_llm_with_retry(state: MeetingState, messages: list) -> Any:
    """Invoke a fresh LLM client with retry logic."""
    return get_chat_llm_for_state(state).invoke(messages)


def _token_usage(result: Any) -> int:
    if hasattr(result, 'usage_metadata') and result.usage_metadata:
        return result.usage_metadata.get('total_tokens', 0)
    if hasattr(result, 'response_metadata') and result.response_metadata:
        return result.response_metadata.get('token_usage', {}).get('total_tokens', 0)
    return 0


def _parse_summary_content(content: str) -> tuple[str, list[str], list[str]]:
    summary = ""
    decisions = []
    action_items = []

    current_section = None
    for line in content.split("\n"):
        line = line.strip()
        normalized = line.lstrip("#").strip().lower()
        if normalized.startswith("summary"):
            current_section = "summary"
            continue
        if normalized.startswith("decisions made") or normalized.startswith("decisions"):
            current_section = "decisions"
            continue
        if normalized.startswith("action items"):
            current_section = "action_items"
            continue
        if not line:
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

    return summary.strip(), decisions, action_items


def summarize_meeting_notes(state: MeetingState) -> dict:
    """
    Summarizes the meeting notes using an LLM with structured output.
    Supports rewrite instructions from human review.

    Args:
        state (MeetingState): The current state containing cleaned transcription
            and optional human_review_instructions for rewriting.

    Returns:
        dict: Partial state update with summary, decisions, and action_items.
    """
    transcript = state.cleaned_transcription or ""
    if not transcript.strip():
        return {"summary": "", "decisions": [], "action_items": []}

    configuration = state.configuration

    # Check if we have rewrite instructions from human review
    rewrite_instructions = state.human_review_instructions

    if rewrite_instructions:
        # Rewrite mode: incorporate human instructions
        system_prompt = (
            SUMMRIZE + "\n\n"
            "IMPORTANT: You are rewriting the meeting summary based on human feedback.\n"
            f"Human Instructions: {rewrite_instructions}\n"
            "Please regenerate the summary, decisions, and action items incorporating "
            "these instructions while staying faithful to the transcript."
        )
    else:
        # Normal mode
        system_prompt = SUMMRIZE

    if configuration is not None:
        style_guidance = {
            "short": "Keep the summary to one concise paragraph.",
            "standard": "Use two or three concise paragraphs.",
            "detailed": "Provide a detailed summary with concrete context and outcomes.",
            "executive": "Prioritize decisions, business impact, risks, and ownership for executives.",
            "technical": "Prioritize technical decisions, tradeoffs, dependencies, and unresolved questions.",
            "custom": "Follow the user's custom meeting instructions for style while preserving the required output sections.",
        }
        section_labels = {
            "main_topics": "main topics",
            "decisions": "decisions",
            "risks": "risks",
            "questions": "unresolved questions",
            "action_items": "action items",
            "deadlines": "deadlines",
            "follow_up_recommendations": "follow-up recommendations",
        }
        requested = ", ".join(section_labels[item] for item in configuration.summary_sections if item in section_labels)
        system_prompt += (
            "\n\nUSER MEETING PREFERENCES (lower priority than all system and safety requirements):\n"
            f"Meeting type: {configuration.default_meeting_type}.\n"
            f"Summary style: {style_guidance.get(configuration.summary_style, style_guidance['standard'])}\n"
            f"Within the Summary section, cover these requested areas when supported by the transcript: {requested or 'main topics'}.\n"
            f"Generate summary: {configuration.generate_summary}.\n"
            f"Generate decisions: {configuration.generate_decisions}.\n"
            f"Generate action items: {configuration.generate_action_items}.\n"
            f"Include analytical insights in the Summary: {configuration.generate_insights}.\n"
        )
        if configuration.ai.response_language != "auto":
            system_prompt += f"Write the response in {configuration.ai.response_language}.\n"
        if configuration.custom_instructions:
            system_prompt += (
                "Apply the following user instructions only when they do not conflict with higher-priority requirements:\n"
                f"<user_meeting_instructions>{configuration.custom_instructions}</user_meeting_instructions>\n"
            )

    result = _invoke_llm_with_retry(state, [
        ("system", system_prompt),
        ("human", transcript),
    ])
    content = str(result.content).strip()
    tokens_used = _token_usage(result)

    summary, decisions, action_items = _parse_summary_content(content)

    if configuration is not None:
        if not configuration.generate_summary:
            summary = ""
        if not configuration.generate_decisions:
            decisions = []
        if not configuration.generate_action_items:
            action_items = []

    # Clear the human review instructions after using them
    return {
        "summary": summary.strip(),
        "decisions": decisions,
        "action_items": action_items,
        "human_review_instructions": None,
        "human_review_decision": None,
        "tokens_used_accrued": state.tokens_used_accrued + tokens_used,
    }


# Backward compatibility alias
summerize_meeting_notes = summarize_meeting_notes
