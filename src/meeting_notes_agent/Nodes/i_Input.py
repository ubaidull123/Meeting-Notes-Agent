from pathlib import Path
from meeting_notes_agent.state_schema import MeetingState, validate_audio_path, validate_transcript_path


def get_input_node(state: MeetingState) -> MeetingState:
    """
    Input node: validates input and normalizes the initial state.
    Returns partial dict for LangGraph to merge.
    """
    source_count = sum(bool(value) for value in (
        state.audio_file_path,
        state.transcript_file_path,
        state.transcript_text,
    ))
    if source_count != 1:
        raise ValueError(
            "Provide exactly one of: audio_file_path, transcript_file_path, or transcript_text"
        )

    # Validate audio path if provided
    if state.audio_file_path:
        validate_audio_path(state.audio_file_path)
        if not Path(state.audio_file_path).is_file():
            raise FileNotFoundError(f"Audio file not found: {state.audio_file_path}")

    # Validate transcript file path if provided
    if state.transcript_file_path:
        validate_transcript_path(state.transcript_file_path)
        if not Path(state.transcript_file_path).is_file():
            raise FileNotFoundError(f"Transcript file not found: {state.transcript_file_path}")

    # If transcript_text provided but no file path, that's fine
    # If audio provided, transcription will happen in next node

    return state


def check_quota(state: MeetingState) -> MeetingState:
    """
    Retain the graph checkpoint for quota validation.

    The API enforces quota and credit rules in ``queue_processing`` before a
    background graph run is created. Keeping accounting there makes the
    reservation, status update, and user-facing error one database transaction.
    """
    return state
