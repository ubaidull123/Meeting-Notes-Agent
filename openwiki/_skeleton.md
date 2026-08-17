---
type: "Reference"
title: "OpenWiki Skeleton — meeting-notes-agent"
openwiki_generated: true
---

# OpenWiki Skeleton — meeting-notes-agent

## Repository inventory
- Python 3.13 package `meeting_notes_agent` under `/meeting_notes_agent/`
- Entry: `pyproject.toml` defines `meeting-notes-agent = "meeting_notes_agent:main"` (no `main` module exists; BOTH `meeting_notes_agent/__init__.py` and `meeting_notes_agent/src/__init__.py` are empty; no `main.py` or `cli.py` anywhere)
- Source layout: `meeting_notes_agent/src/`
- `/skills/` directory at repo root — **OpenWiki skills** (`mermaid-diagrams/`, `write-connector/`) for diagram generation and connector writing, NOT agent skill definitions
- `.github/workflows/openwiki-update.yml` — scheduled CI/CD workflow for automated wiki updates, requires secrets: `OPENROUTER_API_KEY`, `OPENWIKI_LANGSMITH_API_KEY`, `LANGSMITH_API_KEY`
- `.git/` exists (initialized repo) but has **no commits**; fetch-depth: 0 required for workflow
- `.env` file exists but is **empty (0 bytes)** — no API keys configured
- `requirements.txt` has **typo**: `langchain-comunity` (missing 'm') vs `pyproject.toml` correct `langchain-community`
- No tests, no scripts
- Dependencies: langchain, langgraph, pydantic, groq/openai/openrouter/huggingface clients, dotenv

## Existing docs
- `/README.md` — describes an aspirational 13-step pipeline (steps 01–13) with models, integrations (Trello/Notion), email (Gmail/SendGrid), SQLite storage, human-in-the-loop checkpoints, UI components, prompts. **Actual code only implements**: Step 1 (Input validation), Step 2 (Transcribe via Groq Whisper), Step 3 (Clean via OpenAI LLM). Step 4 (Summarize) exists as `iv_summerize.py` but is broken and not integrated. Steps 5–13 have **zero implementation** (no integrations, no UI, no storage, no email, no task creation).
- `/AGENTS.md`, `/CLAUDE.md` — **contain OPENWIKI:START/END block** with specific instructions: "Treat source code and tests as authoritative. A brief's unknowns and review items are verification gaps, not automatic requirements. Prefer the narrowest quiet validation that proves the changed behavior. Preserve complete failure output. The scheduled OpenWiki GitHub Actions workflow refreshes the repository wiki. Do not hand-edit generated OpenWiki pages unless explicitly asked; prefer updating source code/docs and letting OpenWiki regenerate."
- `/openwiki/INSTRUCTIONS.md` — "A code wiki for this repository."

## Ranked components (by runtime importance / centrality)
1. `state_schema.py` — universal state schema (`MeetingState`, `Attendee`, validators) — **canonical state model**
2. `graph.py` — LangGraph StateGraph composition root — **WORKING 3-node pipeline**: uses `MeetingState` as state type; 3 nodes (Input, TranscribeAudio, CleanTranscript) with full edge connectivity (START→Input→TranscribeAudio→CleanTranscript→END); compiles successfully via `graph.compile()`; Summarize node NOT integrated
3. `Nodes/i_Input.py` — returns `MeetingState` (full object); validates audio/transcript paths
4. `Nodes/ii_transcribe_audio.py` — returns `dict` (partial); uses Groq Whisper; falls back to transcript file/text
5. `Nodes/iii_clean_transcript.py` — returns `dict` (partial); uses OpenAI LLM for cleaning
6. `Nodes/iv_summerize.py` — **orphaned, not in graph**: returns `MeetingState` (full but **INCOMPLETE**); **semantic bug**: creates new MeetingState with only `cleaned_transcription` and empty `summary`, invokes LLM, then returns ANOTHER new MeetingState with ONLY `summary` field — **discards all other state** (meeting_id, title, attendees, raw_transcription, decisions, action_items, etc.); function name misspelled "summerize"; not imported or integrated into graph
7. `data/input/meeting_data.py` — **backward-compat shim**: re-exports `Attendee`, `MeetingState` (as `MeetingData`), `MeetingState`, validators, `AudioFormat` from `state_schema`; provides `MeetingInput = MeetingState` alias; no commented-out code; imports work correctly
8. `data/input/audio.py` — audio/transcript path validators — **duplicates validators in state_schema.py**; state_schema.py line 74 claims "moved from audio.py for single source of truth" but **redefines them inline** instead of importing — misleading comment
9. `llms/API_Based/groq.py` — `get_groq_llm()` uses `model=""` (empty string), `get_groq_whisper_llm()` uses `model="whisper"` — **invalid model names**
10. `llms/API_Based/openai.py` — `get_openai_llm()` uses `model="gpt-5.6-luna"` (does not exist), `get_openai_whisper_llm()` uses `model="whisper-large-v3"` — **invalid model names**
11. `llms/API_Based/openrouter.py` — same invalid models as OpenAI
12. `llms/Local/hf/whisper.py` — **EAGER MODEL LOADING + INFERENCE AT IMPORT TIME**: loads ~3GB Whisper model, creates pipeline, AND executes `llm.invoke("path/to/audio.wav")` + `print(result)` at module level (lines 13-40) — **unusable as library**; not used by any node (TranscribeAudio uses Groq Whisper only)
13. `llms/Local/ollama/` — empty directory (placeholder)
14. `meeting_notes_agent/src/database/postgresdb.py` — **EMPTY FILE** (0 bytes), no PostgresCheckpoint implementation
15. `pyproject.toml` — packaging config; **misconfigured entrypoint** (`meeting_notes_agent:main` doesn't exist)
16. `meeting_notes_agent/src/data/transcripts/` — empty directory, intended for cached cleaned transcripts per README, no code writes to it

## Wiki page plan
1. `/openwiki/quickstart.md` — entrypoint, map, task routing
2. `/openwiki/architecture/overview.md` — system architecture, runtime flow, gap between README plan and actual code
3. `/openwiki/architecture/state-schema.md` — `MeetingState`, `Attendee`, validators; **type system conflict**: Pydantic `MeetingState` vs node return types (full `MeetingState` vs `dict` partials) vs `MeetingInput` alias; `AudioFormat` dynamic type vs Enum conflict
4. `/openwiki/architecture/graph.md` — LangGraph StateGraph composition: **document current working 3-node pipeline** — uses `MeetingState`, 3 nodes (Input, TranscribeAudio, CleanTranscript) with full edge connectivity, compiles successfully; **Summarize node NOT integrated** (orphaned in iv_summerize.py)
5. `/openwiki/architecture/nodes/input.md` — Input node (validation, normalization; returns full MeetingState)
6. `/openwiki/architecture/nodes/transcribe.md` — TranscribeAudio node (Groq Whisper, fallback to file/text; returns dict partial)
7. `/openwiki/architecture/nodes/clean.md` — CleanTranscript node (OpenAI LLM cleaning; returns dict partial)
8. `/openwiki/architecture/nodes/summarize.md` — **Summarize node (ORPHANED, NOT IN GRAPH)**: **semantic data loss bug** (returns MeetingState with ONLY summary field, discarding all pipeline state), misspelled function name "summerize", not imported or connected in graph
9. `/openwiki/components/data-models.md` — **Actual models**: `MeetingState` (canonical), `MeetingInput` (alias to MeetingState), `MeetingData` (alias to MeetingState), `AudioFormat` (dynamic type with MP3=".mp3" etc attributes); no commented-out classes; re-exported via meeting_data.py shim
10. `/openwiki/components/validation.md` — audio/transcript path validation **duplication**; state_schema.py misleading comment "single source of truth" but redefines inline; audio.py still has duplicate definitions; neither imports the other
11. `/openwiki/components/llm-providers.md` — Groq / OpenAI / OpenRouter / HuggingFace clients; **invalid model names** (empty string, non-existent "gpt-5.6-luna"); **HF Whisper executes inference at import time** with hardcoded path; unused local models; empty Ollama dir
12. `/openwiki/components/database.md` — PostgresCheckpoint: **empty file, not implemented** (0 bytes at `meeting_notes_agent/src/database/postgresdb.py`)
13. `/openwiki/configuration.md` — env, pyproject, dependencies; **missing CLI entrypoint**, packaging misconfig; **requirements.txt typo** `langchain-comunity`; `.env` empty (0 bytes)
14. `/openwiki/testing.md` — **no tests exist**, graph compiles but untestable without LLM keys, recommended testing approach
15. `/openwiki/README-aspiration.md` — gap between README's 13-step plan and actual code: Graph implements Steps 1-3 only (Input→Transcribe→Clean→END). Step 4 (Summarize) exists as broken orphaned node (iv_summerize.py) but NOT integrated. Steps 5-13 have zero implementation (no integrations, no UI, no storage, no email, no task creation).
16. `/openwiki/openwiki-automation.md` — CI/CD workflow (`.github/workflows/openwiki-update.yml`), required secrets (`OPENROUTER_API_KEY`, `OPENWIKI_LANGSMITH_API_KEY`, `LANGSMITH_API_KEY`), skills configuration (`/skills/mermaid-diagrams/`, `/skills/write-connector/`), mermaid diagram validation, connector writing skill

## Evidence notes
- All source files read in full.
- No tests exist to verify behavior.
- `.git` exists but has no commits (initialized repo).
- README diagram describes planned 13-step pipeline; graph implements 3 working nodes (Input→Transcribe→Clean→END); iv_summerize.py exists as orphaned broken node not in graph.
- Current blockers: invalid model names (empty string, non-existent "gpt-5.6-luna"), HF Whisper eager loading + inference at import time, missing CLI entrypoint (meeting_notes_agent:main doesn't exist), empty .env, requirements.txt typo, no tests, Summarize node not integrated.
- `/skills/` contains OpenWiki skills (mermaid-diagrams, write-connector), not agent skill definitions.
- AGENTS.md/CLAUDE.md contain OpenWiki operational guidance (OPENWIKI:START/END block with specific instructions), not just "OpenWiki guidance only".