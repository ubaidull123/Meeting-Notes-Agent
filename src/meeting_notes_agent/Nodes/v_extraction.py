from typing import Any

from meeting_notes_agent.llms.providers import get_chat_llm_for_state
from meeting_notes_agent.llms.prompts.extract_decisions_prompt import EXTRACTION
from meeting_notes_agent.utils.retry import llm_retry
from meeting_notes_agent.state_schema import MeetingState

@llm_retry
def _invoke_llm_with_retry(state: MeetingState, messages: list) -> Any:
    """Invoke a fresh LLM client with retry logic."""
    return get_chat_llm_for_state(state).invoke(messages)


def extract_meeting_data(state: MeetingState) -> dict:
    """
    Extracts meeting data from the transcript using an LLM.

    Args:
        state (MeetingState): Current state containing transcript.
    Returns:
        dict: A dictionary containing extracted meeting data and token usage.
    """
    transcript = state.cleaned_transcription or state.raw_transcription or ""
    if not transcript.strip():
        return {"extracted_data": "", "tokens_used_accrued": state.tokens_used_accrued}

    system_prompt = EXTRACTION

    messages = [
        ("system", system_prompt),
        ("human", transcript),
    ]

    result = _invoke_llm_with_retry(state, messages)

    # Track token usage
    tokens_used = 0
    if hasattr(result, 'usage_metadata') and result.usage_metadata:
        tokens_used = result.usage_metadata.get('total_tokens', 0)
    elif hasattr(result, 'response_metadata') and result.response_metadata:
        tokens_used = result.response_metadata.get('token_usage', {}).get('total_tokens', 0)

    return {
        "extracted_data": result.content,
        "tokens_used_accrued": state.tokens_used_accrued + tokens_used,
    }
