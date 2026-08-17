# Files

- [Data Models — MeetingState, MeetingInput, MeetingData, Attendee, AudioFormat](data-models.md) - Actual vs aspirational data models: MeetingState (canonical Pydantic model), MeetingInput/MeetingData (aliases to MeetingState), Attendee sub-model, AudioFormat dynamic type vs removed Enum, backward-compat shim in meeting_data.py.
- [Database — PostgresCheckpoint (Not Implemented)](database.md) - PostgresCheckpoint stub: empty postgresdb.py file (0 bytes), no checkpoint implementation, no database integration in graph.
- [LLM Providers — Groq, OpenAI, OpenRouter, HuggingFace Factories](llm-providers.md) - LLM client factories for Groq, OpenAI, OpenRouter, and HuggingFace. Critical issues: invalid model names (empty string, non-existent gpt-5.6-luna), HF Whisper eager loading + inference at import time, unused local models, empty Ollama directory.
- [Validation — Audio/Transcript Path Validators, Duplication](validation.md) - Audio and transcript path validators duplicated between state_schema.py and audio.py, misleading 'single source of truth' comment, frozenset constants, validation functions.
