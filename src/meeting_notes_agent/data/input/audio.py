"""Validation helpers for meeting recording and transcript inputs."""
from pathlib import Path

from typing import Final


AUDIO_EXTENSIONS: Final[frozenset[str]] = frozenset({".mp3", ".wav", ".m4a"})
TRANSCRIPT_EXTENSIONS: Final[frozenset[str]] = frozenset({".txt", ".md", ".text", ".transcript"})
def validate_audio_path(path: str) -> str:
    if Path(path).suffix.lower() not in AUDIO_EXTENSIONS:
        raise ValueError("Unsupported audio format. Supported formats: MP3, WAV, M4A")
    return path
def validate_transcript_path(path: str) -> str:
    if Path(path).suffix.lower() not in TRANSCRIPT_EXTENSIONS:
        raise ValueError("Unsupported transcript format. Use TXT, MD, or a text transcript file.")
    return path
