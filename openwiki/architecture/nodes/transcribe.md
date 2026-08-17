---
type: "Architecture"
title: "TranscribeAudio Node — Groq Whisper Transcription"
description: "TranscribeAudio node: transcribes audio via Groq Whisper API, falls back to reading transcript file or using direct transcript_text. Returns partial dict with raw_transcription."
tags: ["architecture", "node", "transcribe", "groq", "whisper", "audio", "langgraph"]
---

# TranscribeAudio Node — Groq Whisper Transcription

## Source

**File**: `src/Nodes/ii_transcribe_audio.py`

```python
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
```

## Responsibilities

| Responsibility | Implementation |
|----------------|----------------|
| Use direct transcript text | Priority 1: `state.transcript_text` → returns directly |
| Read transcript file | Priority 2: `state.transcript_file_path` → reads file |
| Transcribe audio | Priority 3: `state.audio_file_path` → Groq Whisper API |
| Save transcription (utility) | `save_transcription_to_file()` — not used in graph |

## Priority Logic

```mermaid
flowchart TD
    Start[TranscribeAudio Node] --> HasText{transcript_text?}
    HasText -->|Yes| ReturnText[Return transcript_text]
    HasText -->|No| HasFile{transcript_file_path?}
    HasFile -->|Yes| ReadFile[Read file content]
    ReadFile --> ReturnFile[Return file content]
    HasFile -->|No| HasAudio{audio_file_path?}
    HasAudio -->|Yes| InvokeWhisper[llm.invoke(audio_path)]
    InvokeWhisper --> ReturnAudio[Return transcription]
    HasAudio -->|No| ReturnEmpty[Return empty string]
```

## LLM Provider: Groq Whisper

**Factory**: `get_groq_whisper_llm()` from `src/llms/API_Based/groq.py`

```python
def get_groq_whisper_llm():
    return ChatGroq(model="whisper")  # QUESTIONABLE MODEL NAME
```

**Critical Issue**: `model="whisper"` — Groq's Whisper model is typically:
- `whisper-large-v3`
- `whisper-large-v3-turbo`

The name `"whisper"` alone may not be valid and will likely fail at runtime.

## Return Type: Partial Dict

```python
return {"raw_transcription": transcription}  # Partial update
```

**Correct LangGraph pattern** — only the changed field is returned for state merging.

## Integration in Graph

**File**: `src/graph.py`

```python
graph.add_node("TranscribeAudio", transcribe_audio)
graph.add_edge("Input", "TranscribeAudio")
graph.add_edge("TranscribeAudio", "CleanTranscript")
```

Position: **Second node** after Input, before CleanTranscript.

## State Transitions

| Input State | Output State Update |
|-------------|---------------------|
| `transcript_text="Hello"` | `{"raw_transcription": "Hello"}` |
| `transcript_file_path="meeting.txt"` | `{"raw_transcription": "<file content>"}` |
| `audio_file_path="meeting.mp3"` | `{"raw_transcription": "<Whisper output>"}` |
| None (shouldn't happen) | `{"raw_transcription": ""}` |

## Utility Function (Unused in Graph)

```python
def save_transcription_to_file(transcription: str, output_file_path: str) -> None:
    """Saves the transcribed text to a specified file."""
    with open(output_file_path, "w") as f:
        f.write(transcription)
```

**Not called anywhere** in current codebase. The README mentions `data/transcripts/` for cached transcripts but no code writes there.

## Error Handling

| Error | Cause | Current Handling |
|-------|-------|------------------|
| FileNotFoundError | Transcript file doesn't exist | Propagates (no try/except) |
| Groq API Error | Invalid API key, rate limit, bad model | Propagates (no retry) |
| Invalid model name | `model="whisper"` not recognized | Fails at invoke time |
| Audio file not found | `audio_file_path` invalid | Whisper API error |

**No error handling** — exceptions bubble up to graph execution.

## Testing (Requires API Key + Fixed Model)

```python
from meeting_notes_agent.src.Nodes.ii_transcribe_audio import transcribe_audio
from meeting_notes_agent.src.state_schema import MeetingState
from datetime import date
from unittest.mock import patch

# Test with transcript_text (no API needed)
def test_transcribe_text():
    state = MeetingState(
        meeting_title="Test",
        meeting_date=date.today(),
        transcript_text="Direct transcript"
    )
    result = transcribe_audio(state)
    assert result["raw_transcription"] == "Direct transcript"

# Test with transcript file (mock file)
def test_transcribe_file(tmp_path):
    transcript_file = tmp_path / "test.txt"
    transcript_file.write_text("File transcript")
    
    state = MeetingState(
        meeting_title="Test",
        meeting_date=date.today(),
        transcript_file_path=str(transcript_file)
    )
    result = transcribe_audio(state)
    assert result["raw_transcription"] == "File transcript"

# Test with audio (mock Groq)
@patch("meeting_notes_agent.src.Nodes.ii_transcribe_audio.llm")
def test_transcribe_audio_mock(mock_llm):
    mock_llm.invoke.return_value = "Transcribed from audio"
    
    state = MeetingState(
        meeting_title="Test",
        meeting_date=date.today(),
        audio_file_path="test.mp3"
    )
    result = transcribe_audio(state)
    assert result["raw_transcription"] == "Transcribed from audio"
    mock_llm.invoke.assert_called_once_with("test.mp3")
```

## Required Fixes for Execution

1. **Fix model name** in `groq.py`:
   ```python
   def get_groq_whisper_llm():
       return ChatGroq(model="whisper-large-v3")  # or whisper-large-v3-turbo
   ```

2. **Add API key** to `.env`:
   ```bash
   GROQ_API_KEY=your_groq_api_key
   ```

3. **Add error handling** (optional but recommended):
   ```python
   def transcribe_audio(state: MeetingState) -> dict:
       try:
           # ... existing logic ...
       except Exception as e:
           return {"raw_transcription": "", "error": str(e)}
   ```

## Related Pages

- [Graph Composition](/openwiki/architecture/graph.md) — Node in pipeline
- [Input Node](/openwiki/architecture/nodes/input.md) — Precedes this node
- [Clean Node](/openwiki/architecture/nodes/clean.md) — Follows this node
- [LLM Providers](/openwiki/components/llm-providers.md) — Groq Whisper details
- [State Schema](/openwiki/architecture/state-schema.md) — MeetingState, raw_transcription field
- [Configuration](/openwiki/configuration.md) — API key setup