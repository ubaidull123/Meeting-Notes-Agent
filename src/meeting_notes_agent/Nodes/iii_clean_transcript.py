import re

from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.llms.providers import get_chat_llm_for_state
from meeting_notes_agent.utils.retry import llm_retry


@llm_retry
def _invoke_llm_with_retry(state: MeetingState, messages: list):
    """Use a fresh client so .env credential changes take effect."""
    return get_chat_llm_for_state(state).invoke(messages)


def clean_transcript(state: MeetingState) -> dict:
    """
    Cleans the raw transcription by removing filler words, fixing formatting,
    and adding speaker labels if missing.
    Returns partial state update with cleaned_transcription.
    """
    transcript = state.raw_transcription or ""
    if not transcript.strip():
        return {"cleaned_transcription": "", "tokens_used_accrued": state.tokens_used_accrued}

    system_prompt = (
        "You are a transcription cleaner. Given a raw meeting transcript, "
        "perform the following:\n"
        "1. Remove filler words like 'um', 'uh', 'like', 'you know'\n"
        "2. Fix capitalization and punctuation\n"
        "3. Preserve reliable speaker names already present in the source. Never invent labels such as "
        "'Speaker 1' or 'Speaker 2'. If speakers are unknown, write natural unlabelled paragraphs.\n"
        "4. Collapse multiple blank lines into one\n"
        "5. Remove non-speech artifacts like [inaudible], [music], etc.\n"
        "Return ONLY the cleaned transcript, nothing else."
    )

    messages = [
        ("system", system_prompt),
        ("human", transcript),
    ]

    result = _invoke_llm_with_retry(state, messages)
    cleaned = result.content if hasattr(result, "content") else str(result)
    # Older runs and some transcription models emit anonymous speaker tags even
    # when no speaker identity can be established. They add no useful context to
    # a meeting note, so leave those paragraphs naturally unlabelled.
    cleaned = re.sub(r"(?mi)^speaker\s+\d+\s*:\s*", "", str(cleaned))
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    # Track token usage
    tokens_used = 0
    if hasattr(result, 'usage_metadata') and result.usage_metadata:
        tokens_used = result.usage_metadata.get('total_tokens', 0)
    elif hasattr(result, 'response_metadata') and result.response_metadata:
        tokens_used = result.response_metadata.get('token_usage', {}).get('total_tokens', 0)

    return {
        "cleaned_transcription": cleaned,
        "tokens_used_accrued": state.tokens_used_accrued + tokens_used,
    }
