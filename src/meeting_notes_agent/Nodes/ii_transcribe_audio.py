import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator

from openai import BadRequestError
from meeting_notes_agent.llms.providers import transcribe_file_for_state
from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.utils.retry import llm_retry


# Keep chunks below OpenAI's 25 MiB transcription request limit and short enough
# that long meetings do not go through the transcription model as one request.
# Re-encoding to mono 16 kHz / 64 kbps is appropriate for meeting speech and
# keeps chunk sizes predictable even when the original recording has high bitrate.
MAX_TRANSCRIPTION_BYTES = 24 * 1024 * 1024
CHUNK_SECONDS = 10 * 60


def _audio_chunks(path: Path, output_dir: Path) -> Iterator[Path]:
    """Yield API-safe MP3 chunks for a recording."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "This recording requires FFmpeg for automatic chunking. "
            "Install FFmpeg or upload a smaller recording."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / "chunk-%03d.mp3"
    completed = subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(path), "-vn",
            "-ac", "1", "-ar", "16000", "-b:a", "64k", "-f", "segment",
            "-segment_time", str(CHUNK_SECONDS), "-reset_timestamps", "1",
            str(output_pattern),
        ],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    chunks = sorted(output_dir.glob("chunk-*.mp3"))
    if completed.returncode != 0 or not chunks:
        raise ValueError(
            "Audio file could not be decoded. Please upload a valid MP3, WAV, or M4A recording."
        )
    for chunk in chunks:
        if chunk.stat().st_size > MAX_TRANSCRIPTION_BYTES:
            raise RuntimeError("Audio chunk exceeds the transcription service size limit.")
        yield chunk


def transcribe_audio_file(audio_file_path: str, state: MeetingState) -> str:
    """Transcribe an uploaded recording, chunking long audio before API calls."""
    path = Path(audio_file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {path}")
    @llm_retry
    def transcribe_one(audio_path: Path) -> str:
        try:
            return transcribe_file_for_state(state, audio_path)
        except BadRequestError as exc:
            raise ValueError(
                "The transcription service could not read this audio file. "
                "Upload a valid MP3, WAV, or M4A recording."
            ) from exc

    ffmpeg_available = shutil.which("ffmpeg") is not None
    if not ffmpeg_available and path.stat().st_size <= MAX_TRANSCRIPTION_BYTES:
        return transcribe_one(path)

    if not ffmpeg_available:
        raise RuntimeError(
            "This recording is too large for one transcription request and FFmpeg is not installed. "
            "Install FFmpeg so the app can split long audio automatically."
        )

    with tempfile.TemporaryDirectory(prefix="meeting-transcription-") as temp_dir:
        chunks = _audio_chunks(path, Path(temp_dir))
        transcripts = [transcribe_one(chunk).strip() for chunk in chunks]
    return "\n\n".join(text for text in transcripts if text)


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
        return {"raw_transcription": transcribe_audio_file(state.audio_file_path, state)}

    # Should not reach here if input validation passed
    return {"raw_transcription": ""}


def save_transcription_to_file(transcription: str, output_file_path: str) -> None:
    """Saves the transcribed text to a specified file."""
    with open(output_file_path, "w") as f:
        f.write(transcription)
