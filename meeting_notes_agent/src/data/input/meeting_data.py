"""
Backward-compatibility shim — re-exports from state_schema.
New code should import directly from src.state_schema.
"""
from src.state_schema import (
    Attendee,
    MeetingState as MeetingData,
    MeetingState,
    validate_audio_path,
    validate_transcript_path,
    AudioFormat,
)

# Legacy alias for MeetingInput (was separate model, now same as MeetingState)
MeetingInput = MeetingState