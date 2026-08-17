from src.state_schema import MeetingState
from src.llms.API_Based.groq import get_groq_whisper_llm


llm = get_groq_whisper_llm()


def transcribe_audio(state: MeetingState) -> dict:
    """
    Transcribes the audio file if provided.
    If transcript already present (from file or text), skips transcription.
    Returns partial state update.
    """
    # If transcript already available, skip transcription
    if state.transcript_text:
        return {"raw_transcription": state.transcript_text}

    if state.transcript_file_path:
        with open(state.transcript_file_path, "r") as f:
            return {"raw_transcription": f.read()}

    # Audio provided — transcribe using Whisper
    if state.audio_file_path:
        transcription = llm.invoke(state.audio_file_path)
        return {"raw_transcription": transcription}

    # Should not reach here if input validation passed
    return {"raw_transcription": ""}


def save_transcription_to_file(transcription: str, output_file_path: str) -> None:
    """Saves the transcribed text to a specified file."""
    with open(output_file_path, "w") as f:
        f.write(transcription)