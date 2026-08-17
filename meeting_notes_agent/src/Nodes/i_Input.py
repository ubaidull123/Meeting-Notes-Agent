from src.state_schema import MeetingState, validate_audio_path, validate_transcript_path


def get_input_node(state: MeetingState) -> MeetingState:
    """
    Input node: validates input and normalizes the initial state.
    Returns partial dict for LangGraph to merge.
    """
    # Validate audio path if provided
    if state.audio_file_path:
        validate_audio_path(state.audio_file_path)

    # Validate transcript file path if provided
    if state.transcript_file_path:
        validate_transcript_path(state.transcript_file_path)

    # If transcript_text provided but no file path, that's fine
    # If audio provided, transcription will happen in next node

    return state