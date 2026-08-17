---
type: "Component"
title: "Validation — Audio/Transcript Path Validators, Duplication"
description: "Audio and transcript path validators duplicated between state_schema.py and audio.py, misleading 'single source of truth' comment, frozenset constants, validation functions."
tags: ["component", "validation", "audio", "transcript", "path", "validator", "duplication"]
---

# Validation — Audio/Transcript Path Validators, Duplication

## Two Locations, Same Logic

| File | Purpose | Status |
|------|---------|--------|
| `src/state_schema.py` lines 74-92 | Canonical validators + constants | **Primary** (used by nodes) |
| `src/data/input/audio.py` lines 7-16 | Duplicate validators + constants | **Duplicate** (unused by nodes) |

## In state_schema.py (Canonical)

**Source**: `src/state_schema.py` lines 74-93

```python
# Audio format constants (moved from audio.py for single source of truth)
AUDIO_EXTENSIONS: frozenset[str] = frozenset({".mp3", ".wav", ".m4a"})
TRANSCRIPT_EXTENSIONS: frozenset[str] = frozenset({".txt", ".md", ".text", ".transcript"})


def validate_audio_path(path: str) -> str:
    """Validate audio file extension."""
    from pathlib import Path
    if Path(path).suffix.lower() not in AUDIO_EXTENSIONS:
        raise ValueError("Unsupported audio format. Supported formats: MP3, WAV, M4A")
    return path


def validate_transcript_path(path: str) -> str:
    """Validate transcript file extension."""
    from pathlib import Path
    if Path(path).suffix.lower() not in TRANSCRIPT_EXTENSIONS:
        raise ValueError("Unsupported transcript format. Use TXT, MD, or a text transcript file.")
    return path
```

**Misleading comment**: Line 74 says "moved from audio.py for single source of truth" but **redefines inline** instead of importing from `audio.py`. The `audio.py` file still exists with identical code.

## In audio.py (Duplicate)

**Source**: `src/data/input/audio.py`

```python
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
```

## Comparison

| Aspect | state_schema.py | audio.py |
|--------|-----------------|----------|
| Constants | `AUDIO_EXTENSIONS`, `TRANSCRIPT_EXTENSIONS` (frozenset) | `AUDIO_EXTENSIONS`, `TRANSCRIPT_EXTENSIONS` (Final[frozenset]) |
| Functions | `validate_audio_path`, `validate_transcript_path` | Same names, same logic |
| Import style | `from pathlib import Path` inside function | `from pathlib import Path` at module level |
| Used by nodes | **Yes** (`i_Input.py` imports from state_schema) | **No** |
| Comment | "moved from audio.py for single source of truth" | None |

## Which Is Actually Used?

**Nodes import from state_schema**:

```python
# src/Nodes/i_Input.py
from src.state_schema import MeetingState, validate_audio_path, validate_transcript_path
```

**audio.py is NOT imported by any node**.

## Why Duplication Exists

1. **Historical**: `audio.py` was created first with validators
2. **Refactor attempt**: Comment in state_schema.py claims "moved from audio.py" but didn't actually remove from audio.py or import from it
3. **Backward compat**: `meeting_data.py` shim re-exports validators from state_schema, not audio.py

## Constants Comparison

```python
# Both files define identical frozensets:

# state_schema.py
AUDIO_EXTENSIONS: frozenset[str] = frozenset({".mp3", ".wav", ".m4a"})

# audio.py
AUDIO_EXTENSIONS: Final[frozenset[str]] = frozenset({".mp3", ".wav", ".m4a"})
```

**Difference**: `Final` type hint in audio.py (from `typing` import).

## Validation Logic

### Audio Validation
```python
def validate_audio_path(path: str) -> str:
    suffix = Path(path).suffix.lower()  # e.g., ".mp3"
    if suffix not in {".mp3", ".wav", ".m4a"}:
        raise ValueError("Unsupported audio format. Supported formats: MP3, WAV, M4A")
    return path
```

**Accepted**: `.mp3`, `.wav`, `.m4a` (case-insensitive)
**Rejected**: `.txt`, `.md`, `.ogg`, `.flac`, etc.

### Transcript Validation
```python
def validate_transcript_path(path: str) -> str:
    suffix = Path(path).suffix.lower()  # e.g., ".txt"
    if suffix not in {".txt", ".md", ".text", ".transcript"}:
        raise ValueError("Unsupported transcript format. Use TXT, MD, or a text transcript file.")
    return path
```

**Accepted**: `.txt`, `.md`, `.text`, `.transcript` (case-insensitive)
**Rejected**: `.mp3`, `.wav`, `.pdf`, `.docx`, etc.

## Usage in Input Node

**File**: `src/Nodes/i_Input.py`

```python
def get_input_node(state: MeetingState) -> MeetingState:
    if state.audio_file_path:
        validate_audio_path(state.audio_file_path)  # Raises ValueError if invalid
    if state.transcript_file_path:
        validate_transcript_path(state.transcript_file_path)  # Raises ValueError if invalid
    return state
```

**Behavior**: Validates at graph entry (Input node). Invalid paths cause immediate failure before any processing.

## Model Validator (Additional Check)

**File**: `src/state_schema.py` — `MeetingState` model validator

```python
@model_validator(mode="after")
def validate_input_source(self) -> "MeetingState":
    """Ensure at least one transcript/audio source is provided at entry."""
    has_audio = bool(self.audio_file_path)
    has_transcript_file = bool(self.transcript_file_path)
    has_transcript_text = bool(self.transcript_text)
    if not (has_audio or has_transcript_file or has_transcript_text):
        raise ValueError(
            "Must provide at least one of: audio_file_path, transcript_file_path, or transcript_text"
        )
    return self
```

**Runs at**: `MeetingState` construction time (before graph).

## Error Messages

| Validator | Invalid Input | Error Message |
|-----------|---------------|---------------|
| `validate_audio_path` | `"meeting.txt"` | "Unsupported audio format. Supported formats: MP3, WAV, M4A" |
| `validate_audio_path` | `"meeting.OGG"` | "Unsupported audio format. Supported formats: MP3, WAV, M4A" |
| `validate_transcript_path` | `"meeting.mp3"` | "Unsupported transcript format. Use TXT, MD, or a text transcript file." |
| `validate_transcript_path` | `"meeting.pdf"` | "Unsupported transcript format. Use TXT, MD, or a text transcript file." |
| Model validator | No source at all | "Must provide at least one of: audio_file_path, transcript_file_path, or transcript_text" |

## Recommended Fix

**Option 1**: Remove `audio.py` entirely, keep `state_schema.py` as single source
```bash
rm src/data/input/audio.py
# Update any imports (none currently)
```

**Option 2**: Make `state_schema.py` import from `audio.py`
```python
# In state_schema.py
from src.data.input.audio import AUDIO_EXTENSIONS, TRANSCRIPT_EXTENSIONS
from src.data.input.audio import validate_audio_path, validate_transcript_path
# Remove inline definitions
```

**Option 3**: Keep both but document clearly (current state)

## Testing Validators

```python
from meeting_notes_agent.src.state_schema import validate_audio_path, validate_transcript_path
import pytest

# Audio
assert validate_audio_path("test.mp3") == "test.mp3"
assert validate_audio_path("TEST.WAV") == "TEST.WAV"
with pytest.raises(ValueError, match="Unsupported audio format"):
    validate_audio_path("test.txt")

# Transcript
assert validate_transcript_path("notes.txt") == "notes.txt"
assert validate_transcript_path("notes.MD") == "notes.MD"
with pytest.raises(ValueError, match="Unsupported transcript format"):
    validate_transcript_path("notes.mp3")
```

## Related Pages

- [State Schema](/openwiki/architecture/state-schema.md) — Validators in canonical location
- [Input Node](/openwiki/architecture/nodes/input.md) — Uses validators
- [Data Models](/openwiki/components/data-models.md) — AudioFormat dynamic type
- [meeting_data.py shim](/openwiki/components/data-models.md#backward-compatibility-shim-meeting_datapy) — Re-exports validators