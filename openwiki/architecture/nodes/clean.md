---
type: "Architecture"
title: "CleanTranscript Node — OpenAI LLM Cleaning"
description: "CleanTranscript node: uses OpenAI LLM to clean raw transcription (remove fillers, fix punctuation, label speakers). Returns partial dict with cleaned_transcription."
tags: ["architecture", "node", "clean", "transcript", "openai", "llm", "langgraph"]
---

# CleanTranscript Node — OpenAI LLM Cleaning

## Source

**File**: `src/Nodes/iii_clean_transcript.py`

```python
from src.state_schema import MeetingState
from src.llms.API_Based.openai import get_openai_llm


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
        4. Collapse multiple blank lines into one\n"
        "5. Remove non-speech artifacts like [inaudible], [music], etc.\n"
        "Return ONLY the cleaned transcript, nothing else."
    )

    messages = [
        ("system", system_prompt),
        ("human", transcript),
    ]

    result = llm.invoke(messages)
    return {"cleaned_transcription": result.content}
```

## Responsibilities

| Responsibility | Implementation |
|----------------|----------------|
| Remove filler words | LLM prompt instruction |
| Fix capitalization/punctuation | LLM prompt instruction |
| Label speakers | LLM prompt instruction (Speaker 1:, Speaker 2:, etc.) |
| Collapse blank lines | LLM prompt instruction |
| Remove non-speech artifacts | LLM prompt instruction ([inaudible], [music], etc.) |
| Return cleaned text | `result.content` → `cleaned_transcription` |

## System Prompt

```text
You are a transcription cleaner. Given a raw meeting transcript, 
perform the following:
1. Remove filler words like 'um', 'uh', 'like', 'you know'
2. Fix capitalization and punctuation
3. Label speakers if not already labeled (use 'Speaker 1:', 'Speaker 2:', etc.)
4. Collapse multiple blank lines into one
5. Remove non-speech artifacts like [inaudible], [music], etc.
Return ONLY the cleaned transcript, nothing else.
```

## LLM Provider: OpenAI

**Factory**: `get_openai_llm()` from `src/llms/API_Based/openai.py`

```python
def get_openai_llm():
    return ChatOpenAI(model="gpt-5.6-luna")  # INVALID MODEL NAME
```

**Critical Issue**: `model="gpt-5.6-luna"` — **this model does not exist**. 

Valid OpenAI models (as of 2024):
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

The current model name will cause runtime failure.

## Return Type: Partial Dict

```python
return {"cleaned_transcription": result.content}
```

**Correct LangGraph pattern** — only the changed field is returned.

## Integration in Graph

**File**: `src/graph.py`

```python
graph.add_node("CleanTranscript", clean_transcript)
graph.add_edge("TranscribeAudio", "CleanTranscript")
graph.add_edge("CleanTranscript", END)
```

Position: **Third (last) node** in current graph, connects to END.

## State Transitions

| Input State | Output State Update |
|-------------|---------------------|
| `raw_transcription="Speaker 1: Hello um world"` | `{"cleaned_transcription": "Speaker 1: Hello world."}` |
| `raw_transcription=""` | `{"cleaned_transcription": ""}` |
| `raw_transcription=None` | `{"cleaned_transcription": ""}` |

## Processing Flow

```mermaid
flowchart TD
    Start[CleanTranscript Node] --> CheckRaw{raw_transcription?}
    CheckRaw -->|Empty/None| ReturnEmpty[Return empty string]
    CheckRaw -->|Has Content| BuildPrompt[Build messages with system prompt]
    BuildPrompt --> InvokeLLM[llm.invoke(messages)]
    InvokeLLM --> ReturnClean[Return result.content]
```

## Error Handling

| Error | Cause | Current Handling |
|-------|-------|------------------|
| OpenAI API Error | Invalid API key, rate limit, bad model | Propagates (no try/except) |
| Invalid model name | `gpt-5.6-luna` doesn't exist | Fails at invoke time |
| Empty transcript | `raw_transcription` is None/empty | Returns empty string (handled) |
| LLM returns None | Unexpected response | `.content` may be None |

**No error handling** — exceptions bubble up to graph execution.

## Testing (Requires API Key + Fixed Model)

```python
from meeting_notes_agent.src.Nodes.iii_clean_transcript import clean_transcript
from meeting_notes_agent.src.state_schema import MeetingState
from datetime import date
from unittest.mock import patch, MagicMock

# Test empty transcript
def test_clean_empty():
    state = MeetingState(
        meeting_title="Test",
        meeting_date=date.today(),
        raw_transcription=""
    )
    result = clean_transcript(state)
    assert result["cleaned_transcription"] == ""

# Test with content (mock OpenAI)
@patch("meeting_notes_agent.src.Nodes.iii_clean_transcript.llm")
def test_clean_transcript_mock(mock_llm):
    mock_response = MagicMock()
    mock_response.content = "Speaker 1: Hello world."
    mock_llm.invoke.return_value = mock_response
    
    state = MeetingState(
        meeting_title="Test",
        meeting_date=date.today(),
        raw_transcription="Speaker 1: Hello um world"
    )
    result = clean_transcript(state)
    
    assert result["cleaned_transcription"] == "Speaker 1: Hello world."
    mock_llm.invoke.assert_called_once()
    # Verify messages structure
    call_args = mock_llm.invoke.call_args[0][0]
    assert len(call_args) == 2
    assert call_args[0][0] == "system"
    assert call_args[1][0] == "human"
```

## Required Fixes for Execution

1. **Fix model name** in `openai.py`:
   ```python
   def get_openai_llm():
       return ChatOpenAI(model="gpt-4o-mini")  # or gpt-4o, gpt-3.5-turbo
   ```

2. **Add API key** to `.env`:
   ```bash
   OPENAI_API_KEY=your_openai_api_key
   ```

3. **Add error handling** (optional):
   ```python
   def clean_transcript(state: MeetingState) -> dict:
       try:
           transcript = state.raw_transcription or ""
           if not transcript.strip():
               return {"cleaned_transcription": ""}
           # ... existing logic ...
       except Exception as e:
           return {"cleaned_transcription": "", "clean_error": str(e)}
   ```

## Prompt Engineering Notes

The current prompt is a **single-shot** instruction. For production, consider:
- **Few-shot examples** showing before/after
- **Structured output** (JSON) for parsing speaker labels
- **Temperature control** (lower for consistency)
- **Max tokens** limit

## Related Pages

- [Graph Composition](/openwiki/architecture/graph.md) — Node in pipeline
- [Transcribe Node](/openwiki/architecture/nodes/transcribe.md) — Precedes this node
- [LLM Providers](/openwiki/components/llm-providers.md) — OpenAI details, invalid model
- [State Schema](/openwiki/architecture/state-schema.md) — MeetingState, cleaned_transcription field
- [Configuration](/openwiki/configuration.md) — API key setup
- [Summarize Node](/openwiki/architecture/nodes/summarize.md) — Would follow this node