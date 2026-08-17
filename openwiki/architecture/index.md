# Files

- [Graph Composition — LangGraph StateGraph with 3 Working Nodes](graph.md) - LangGraph StateGraph composition: build_graph() function, 3 nodes (Input, TranscribeAudio, CleanTranscript) with full edge connectivity, compiles successfully, uses MeetingState as state type. Summarize node not integrated.
- [System Architecture — Meeting Notes Agent Pipeline](overview.md) - Overall system architecture: LangGraph StateGraph pipeline with 3 working nodes (Input→Transcribe→Clean), orphaned Summarize node, LLM provider abstraction, state schema, and gap to README's 13-step plan.
- [State Schema — MeetingState, Attendee, Validators, Type Conflicts](state-schema.md) - Canonical MeetingState Pydantic model, Attendee sub-model, validators for audio/transcript paths and input sources, type conflicts (Pydantic vs dict returns vs dynamic AudioFormat).

# Directories

- [nodes](nodes/)
