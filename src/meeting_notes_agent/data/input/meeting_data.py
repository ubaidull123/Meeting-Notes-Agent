"""
Backward-compatibility shim — re-exports from state_schema.
New code should import directly from meeting_notes_agent.state_schema.
"""
from meeting_notes_agent.state_schema import (
    Attendee,
    MeetingState as MeetingData,
    MeetingState,
    validate_audio_path,
    validate_transcript_path,
    AudioFormat,
)

MeetingInput = MeetingState