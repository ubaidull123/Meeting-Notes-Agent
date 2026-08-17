# Files

- [CleanTranscript Node — OpenAI LLM Cleaning](clean.md) - CleanTranscript node: uses OpenAI LLM to clean raw transcription (remove fillers, fix punctuation, label speakers). Returns partial dict with cleaned_transcription.
- [Input Node — Validation & Normalization](input.md) - Input node (get_input_node) validates audio/transcript paths using validators from state_schema, normalizes initial MeetingState. Returns full MeetingState object (unconventional for LangGraph).
- [Summarize Node — Broken, Orphaned, Data Loss Bug](summarize.md) - Summarize node (iv_summerize.py): misspelled function name, invalid OpenAI model, semantic bug discarding all pipeline state except summary, not integrated into graph.
- [TranscribeAudio Node — Groq Whisper Transcription](transcribe.md) - TranscribeAudio node: transcribes audio via Groq Whisper API, falls back to reading transcript file or using direct transcript_text. Returns partial dict with raw_transcription.
