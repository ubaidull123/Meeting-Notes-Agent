---
type: "Reference"
title: "Quickstart — Meeting Notes Agent Wiki"
description: "Entry point for the Meeting Notes Agent code wiki. High-level map, key concepts, task routing table, and navigation guide for understanding the 3-node LangGraph pipeline and its gaps vs. the 13-step README plan."
tags: ["quickstart", "entrypoint", "navigation", "overview"]
---

# Quickstart — Meeting Notes Agent Wiki

This wiki documents the **actual implementation** of the Meeting Notes Agent — a LangGraph-based pipeline that processes meeting audio/transcripts into cleaned transcripts — and the **significant gaps** between the code and the aspirational 13-step pipeline described in `README.md`.

## Repository at a Glance

| Aspect | Status |
|--------|--------|
| **Language** | Python 3.13 |
| **Orchestration** | LangGraph `StateGraph` (3 working nodes) |
| **State Model** | `MeetingState` (Pydantic) — canonical, single source |
| **LLM Providers** | Groq (Whisper), OpenAI (GPT), OpenRouter, HuggingFace (local, broken) |
| **Persistence** | None (PostgresCheckpoint file exists but is empty) |
| **CLI Entrypoint** | ❌ Missing (`meeting_notes_agent:main` doesn't exist) |
| **Tests** | ❌ None |
| **API Keys** | ❌ `.env` is empty |

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH PIPELINE (3 NODES)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│   │  Input   │───▶│ TranscribeAudio │───▶│ CleanTranscript │  │
│   │  Node    │    │   (Groq Whisper)│    │   (OpenAI LLM)  │  │
│   └──────────┘    └─────────────────┘    └────────┬────────┘  │
│                                                    │           │
│                                              ┌─────▼──────┐    │
│                                              │    END     │    │
│                                              └────────────┘    │
│                                                                 │
│   ⚠️  Orphaned: Summarize Node (iv_summerize.py) — broken,      │
│      not in graph, discards all pipeline state                  │
└─────────────────────────────────────────────────────────────────┘
```

**Data Flow**: User creates `MeetingState` → Input validates paths → TranscribeAudio produces `raw_transcription` → CleanTranscript produces `cleaned_transcription` → END.

## Key Concepts (Canonical Pages)

| Concept | Wiki Page | What You'll Learn |
|---------|-----------|-------------------|
| **State Schema** | [architecture/state-schema.md](architecture/state-schema.md) | `MeetingState`, `Attendee`, validators, type conflicts (Pydantic vs partial dict returns) |
| **Graph Composition** | [architecture/graph.md](architecture/graph.md) | `build_graph()`, 3 nodes, edge connectivity, compilation, state merging |
| **Input Node** | [architecture/nodes/input.md](architecture/nodes/input.md) | Path validation, returns full `MeetingState` (unconventional) |
| **Transcribe Node** | [architecture/nodes/transcribe.md](architecture/nodes/transcribe.md) | Groq Whisper, fallback priority (text → file → audio), invalid model name |
| **Clean Node** | [architecture/nodes/clean.md](architecture/nodes/clean.md) | OpenAI LLM cleaning, system prompt, invalid model name |
| **Summarize Node** | [architecture/nodes/summarize.md](architecture/nodes/summarize.md) | **Broken**: misspelled name, data loss bug, wrong return type, not in graph |
| **Data Models** | [components/data-models.md](components/data-models.md) | `MeetingState` (canonical), `MeetingInput`/`MeetingData` (aliases), `AudioFormat` dynamic type |
| **Validation** | [components/validation.md](components/validation.md) | Duplicated validators in `state_schema.py` vs `audio.py`, misleading comment |
| **LLM Providers** | [components/llm-providers.md](components/llm-providers.md) | 4 factories, all have invalid model names, HF eager loading breaks imports |
| **Database** | [components/database.md](components/database.md) | Empty `postgresdb.py`, no checkpoint, no persistence |
| **Configuration** | [configuration.md](configuration.md) | `pyproject.toml` entrypoint broken, `requirements.txt` typo, empty `.env` |
| **Aspiration Gap** | [README-aspiration.md](README-aspiration.md) | 13-step README plan vs 3 working nodes — 9 steps with zero code |
| **Testing** | [testing.md](testing.md) | No tests exist, mocking strategy, verification approach |
| **OpenWiki Automation** | [openwiki-automation.md](openwiki-automation.md) | CI/CD workflow, required secrets, skills, mermaid validation |

## Task Routing Table

Use this table to navigate from a **change intent** to the relevant wiki page, source files, and validation approach.

| Change Intent | Wiki Page | Source Entrypoints | Focused Test / Validation |
|---------------|-----------|-------------------|---------------------------|
| **Understand the pipeline** | [architecture/overview.md](architecture/overview.md) | `src/graph.py`, `src/state_schema.py` | `python -m meeting_notes_agent.src.graph` (compiles) |
<!-- openwiki: broken internal link [configuration.md#missing-entrypoint] heading anchor "missing-entrypoint" does not exist in "configuration.md". Fix the href or restore the target, then delete this comment. -->
| **Fix the CLI entrypoint** | [configuration.md#missing-entrypoint](configuration.md#missing-entrypoint) | `pyproject.toml`, `meeting_notes_agent/__init__.py` | `pip install -e . && meeting-notes-agent --help` |
| **Fix invalid model names** | [components/llm-providers.md](components/llm-providers.md) | `src/llms/API_Based/groq.py`, `openai.py`, `openrouter.py` | Set API keys in `.env`, run graph with transcript_text |
| **Integrate Summarize node** | [architecture/nodes/summarize.md](architecture/nodes/summarize.md) | `src/Nodes/iv_summerize.py`, `src/graph.py` | Mock OpenAI, verify partial dict return preserves state |
| **Add Decisions extraction** | [README-aspiration.md](README-aspiration.md) (Step 5) | New node needed, extend `MeetingState.decisions` | Unit test with structured LLM output |
| **Add Action Items extraction** | [README-aspiration.md](README-aspiration.md) (Step 6) | New node needed, extend `MeetingState.action_items` | Unit test with assignee/deadline parsing |
| **Implement human-in-the-loop** | [README-aspiration.md](README-aspiration.md) (Steps 8, 11) | LangGraph interrupts, checkpointer needed | Integration test with `MemorySaver` |
| **Add PM tool integration** | [README-aspiration.md](README-aspiration.md) (Step 9) | New `pm_integration.py`, Trello/Notion clients | Mock HTTP, verify task creation |
| **Add email drafting/sending** | [README-aspiration.md](README-aspiration.md) (Steps 10-12) | New `emailer.py`, Gmail/SendGrid clients | Mock SMTP/API, verify draft + send |
| **Implement database persistence** | [components/database.md](components/database.md) | `src/database/postgresdb.py`, add checkpointer to graph | SQLite `MemorySaver` test, then Postgres |
| **Fix validator duplication** | [components/validation.md](components/validation.md) | `src/state_schema.py`, `src/data/input/audio.py` | Remove `audio.py`, verify imports still work |
| **Add unit tests** | [testing.md](testing.md) | Create `tests/` directory, pytest config | `pytest tests/unit/` passes with mocks |
| **Fix HF Whisper eager loading** | [components/llm-providers.md](components/llm-providers.md) | `src/llms/Local/hf/whisper.py` | Import module without download/inference |

## Quick Validation Commands

```bash
# 1. Verify graph compiles (no API keys needed)
python -m meeting_notes_agent.src.graph
# Expected: "Graph compiled successfully", lists 3 nodes

# 2. Run pipeline with transcript text (needs fixed OpenAI model + API key)
python run.py  # Create run.py per configuration.md workaround

# 3. Check for import-time side effects (HF Whisper)
python -c "import meeting_notes_agent.src.llms.Local.hf.whisper"
# Should NOT download model or run inference

# 4. Validate environment
cat .env  # Should have GROQ_API_KEY, OPENAI_API_KEY
```

## Current Blockers (Fix These First)

<!-- openwiki: broken internal link [configuration.md#missing-entrypoint] heading anchor "missing-entrypoint" does not exist in "configuration.md". Fix the href or restore the target, then delete this comment. -->
1. **Entrypoint missing** — `meeting_notes_agent:main` doesn't exist ([configuration.md](configuration.md#missing-entrypoint))
2. **Invalid model names** — `gpt-5.6-luna` (OpenAI), `""` (Groq LLM), `"whisper"` (Groq Whisper) ([components/llm-providers.md](components/llm-providers.md))
3. **HF Whisper breaks imports** — eager loading + inference at module level ([components/llm-providers.md](components/llm-providers.md#huggingface-local-whisper))
4. **Empty `.env`** — no API keys for any provider ([configuration.md](configuration.md#env-file))
5. **requirements.txt typo** — `langchain-comunity` → `langchain-community` ([configuration.md](configuration.md#requirementstxt))
6. **Summarize node broken** — data loss, wrong return type, not in graph ([architecture/nodes/summarize.md](architecture/nodes/summarize.md))

## Wiki Navigation Tips

- **Start here** → [architecture/overview.md](architecture/overview.md) for system map
- **Deep dive nodes** → [architecture/nodes/](architecture/nodes/index.md) for each node's logic, prompts, bugs
- **Understand data** → [components/data-models.md](components/data-models.md) for canonical models and aliases
- **See the gap** → [README-aspiration.md](README-aspiration.md) for planned vs implemented
- **Fix config** → [configuration.md](configuration.md) for entrypoint, deps, env
- **Add tests** → [testing.md](testing.md) for strategy and examples

## Backlog (Explicitly Deferred)

| Area | Reason | Source Anchor |
|------|--------|---------------|
| Trello/Notion task clients | Zero implementation, requires PM tool accounts | [README-aspiration.md](README-aspiration.md#missing-integrations-all-zero-implementation) |
| Gmail/SendGrid email clients | Zero implementation, requires email service setup | [README-aspiration.md](README-aspiration.md#missing-integrations-all-zero-implementation) |
| Redaction logic | Zero implementation, heuristic-based | [README-aspiration.md](README-aspiration.md#missing-integrations-all-zero-implementation) |
| Human-in-the-loop UI | Requires LangGraph interrupts + checkpointer | [README-aspiration.md](README-aspiration.md#missing-infrastructure) |
| SQLite/Postgres persistence | Empty `postgresdb.py`, no checkpointer in graph | [components/database.md](components/database.md) |
<!-- openwiki: broken internal link [configuration.md#missing-entrypoint] heading anchor "missing-entrypoint" does not exist in "configuration.md". Fix the href or restore the target, then delete this comment. -->
| Full CLI with args | No entrypoint, no argument parsing | [configuration.md](configuration.md#missing-entrypoint) |

---

*Generated by OpenWiki. For questions about this wiki, see [index.md](index.md) or the [OpenWiki Automation](openwiki-automation.md) page.*