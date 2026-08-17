from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.llms.API_Based.openai import get_openai_llm


llm = get_openai_llm()


def clean_transcript(state: MeetingState) -> dict:
    """
    Cleans the raw transcription by removing filler words, fixing formatting,
    and adding speaker labels if missing.
    Returns partial state update with cleaned_transcription.
    """
    transcript = state.raw_transcription or ""
    if not transcript.strip():
        return {"cleaned_transcription": ""}

    system_prompt = (
        "You are a transcription cleaner. Given a raw meeting transcript, "
        "perform the following:\n"
        "1. Remove filler words like 'um', 'uh', 'like', 'you know'\n"
        "2. Fix capitalization and punctuation\n"
        "3. Label speakers if not already labeled (use 'Speaker 1:', 'Speaker 2:', etc.)\n"
        "4. Collapse multiple blank lines into one\n"
        "5. Remove non-speech artifacts like [inaudible], [music], etc.\n"
        "Return ONLY the cleaned transcript, nothing else."
    )

    messages = [
        ("system", system_prompt),
        ("human", transcript),
    ]

    result = llm.invoke(messages)
    return {"cleaned_transcription": result.content}