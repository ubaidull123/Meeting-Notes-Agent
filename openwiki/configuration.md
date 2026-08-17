---
type: "Configuration"
title: "Configuration — Environment, Packaging, Dependencies, Entrypoint"
description: "Project configuration: pyproject.toml packaging, misconfigured CLI entrypoint (meeting_notes_agent:main doesn't exist), requirements.txt typo (langchain-comunity), empty .env file, dependency versions."
tags: ["configuration", "pyproject", "entrypoint", "requirements", "env", "packaging", "uv"]
---

# Configuration — Environment, Packaging, Dependencies, Entrypoint

## Project Structure

```
meeting-notes-agent/
├── pyproject.toml          # Packaging config (uv build)
├── requirements.txt        # Pip dependencies (HAS TYPO)
├── .env                    # Environment variables (EMPTY)
├── .python-version         # Python 3.13
├── uv.lock                 # Locked dependencies
├── meeting_notes_agent/    # Package root
│   ├── __init__.py         # EMPTY
│   └── src/
│       ├── __init__.py     # EMPTY
│       └── ...             # Source modules
└── .github/workflows/      # CI/CD
```

## pyproject.toml

**File**: `pyproject.toml`

```toml
[project]
name = "meeting-notes-agent"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
authors = [
    { name = "Ubaidullah Saeed", email = "ubaidullahsaeed2006@gmail.com" }
]
requires-python = ">=3.13"
dependencies = [
    "dotenv>=0.9.9",
    "langchain>=1.3.15",
    "langchain-core>=1.5.4",
    "langchain-groq>=1.1.3",
    "langchain-huggingface>=1.2.2",
    "langchain-openai>=1.4.3",
    "langchain-openrouter>=0.2.7",
    "langgraph>=1.2.11",
    "pydantic>=2.12.5",
]

[project.scripts]
meeting-notes-agent = "meeting_notes_agent:main"

[build-system]
requires = ["uv_build>=0.12.3,<0.13.0"]
build-backend = "uv_build"
```

### Issues

| Issue | Location | Impact |
|-------|----------|--------|
| **Misconfigured entrypoint** | `[project.scripts]` line | `meeting_notes_agent:main` — no `main` module exists |
| **Missing dependencies** | `dependencies` | No `langgraph-checkpoint-postgres`, `psycopg` for DB |
| **Version** | `version = "0.1.0"` | Placeholder |
| **Description** | `description` | Placeholder |

## Missing Entrypoint {#missing-entrypoint}

**Declared**: `meeting-notes-agent = "meeting_notes_agent:main"`

**Reality**: 
- `meeting_notes_agent/__init__.py` — **empty** (0 bytes)
- `meeting_notes_agent/src/__init__.py` — **empty** (0 bytes)
- No `main.py`, `cli.py`, or `__main__.py` anywhere

**Result**: `meeting-notes-agent` command fails with `AttributeError: module 'meeting_notes_agent' has no attribute 'main'`

### Fix Options

**Option 1**: Add `main.py` at package root
```python
# meeting_notes_agent/main.py
from meeting_notes_agent.src.graph import graph
from meeting_notes_agent.src.state_schema import MeetingState, Attendee
from datetime import date
import sys

def main():
    app = graph.compile()
    # ... CLI logic ...
    
if __name__ == "__main__":
    main()
```

**Option 2**: Add `__main__.py` in src
```python
# meeting_notes_agent/src/__main__.py
# ... same as above ...
```
And change entrypoint to `meeting_notes_agent.src:main`

**Option 3**: Use `click` or `typer` for proper CLI

## requirements.txt

**File**: `requirements.txt`

```
langchain>=1.3.15
langchain-core>=1.5.4
langchain-groq>=1.1.3
langchain-comunity>=1.3.15    # TYPO: should be langchain-community
langchain-huggingface>=1.2.2
langchain-openai>=1.4.3
langgraph>=1.2.11
pydantic>=2.12.5
python-dotenv>=0.9.9
```

### Critical Issue: Typo

| Line | Current | Correct |
|------|---------|---------|
| 4 | `langchain-comunity>=1.3.15` | `langchain-community>=1.3.15` |

**Impact**: `pip install -r requirements.txt` will fail or install wrong package.

**Note**: `pyproject.toml` does NOT have this dependency listed at all (uses `langchain-huggingface` instead).

## .env File

**File**: `.env`

**Current**: **Empty (0 bytes)**

**Required for execution**:
```bash
# Groq (for TranscribeAudio)
GROQ_API_KEY=your_groq_api_key

# OpenAI (for CleanTranscript, Summarize)
OPENAI_API_KEY=your_openai_api_key

# OpenRouter (if used)
OPENROUTER_API_KEY=your_openrouter_api_key

# Database (if Postgres implemented)
DATABASE_URL=postgresql://user:pass@host:5432/db

# LangSmith (for OpenWiki workflow)
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=meeting-notes-agent
```

## Dependency Versions (from pyproject.toml)

| Package | Version | Purpose |
|---------|---------|---------|
| `dotenv` | `>=0.9.9` | Environment loading |
| `langchain` | `>=1.3.15` | Core LangChain |
| `langchain-core` | `>=1.5.4` | Core abstractions |
| `langchain-groq` | `>=1.1.3` | Groq integration |
| `langchain-huggingface` | `>=1.2.2` | HF integration |
| `langchain-openai` | `>=1.4.3` | OpenAI integration |
| `langchain-openrouter` | `>=0.2.7` | OpenRouter integration |
| `langgraph` | `>=1.2.11` | Graph orchestration |
| `pydantic` | `>=2.12.5` | Data validation |

**Missing from pyproject.toml** (in requirements.txt):
- `langchain-community` (typo in requirements.txt)
- `python-dotenv` (pyproject has `dotenv`)

## Locked Versions (uv.lock)

Key locked versions (from `uv.lock`):
- `langchain==1.3.15`
- `langchain-core==1.5.4`
- `langchain-groq==1.1.3`
- `langchain-huggingface==1.2.2`
- `langchain-openai==1.4.3`
- `langchain-openrouter==0.2.7`
- `langgraph==1.2.11`
- `pydantic==2.12.5`
- `python-dotenv==1.0.1` (note: package name is `python-dotenv`, not `dotenv`)

## Python Version

**File**: `.python-version`
```
3.13
```

## Build System

```toml
[build-system]
requires = ["uv_build>=0.12.3,<0.13.0"]
build-backend = "uv_build"
```

Uses `uv` for building (modern, fast).

## Installation

### Current (Broken)
```bash
# Fails due to entrypoint + requirements typo
pip install -e .
# Or
uv pip install -e .
```

### Working (After Fixes)
```bash
# 1. Fix requirements.txt typo
# 2. Add main.py with entrypoint
# 3. Add .env with API keys
uv pip install -e .
# Or
pip install -e .

# Then run
meeting-notes-agent
```

## Running Without CLI (Current Workaround)

```python
# run.py (create this)
from meeting_notes_agent.src.graph import graph
from meeting_notes_agent.src.state_schema import MeetingState, Attendee
from datetime import date

app = graph.compile()

state = MeetingState(
    meeting_title="Test Meeting",
    meeting_date=date.today(),
    transcript_text="Speaker 1: Hello world",
    attendees=[Attendee(name="Alice", email="alice@example.com")]
)

result = app.invoke(state)
print(result)
```

```bash
python run.py
```

## Related Pages

- [Architecture Overview](/openwiki/architecture/overview.md) — System requiring config
- [Graph Composition](/openwiki/architecture/graph.md) — Compilation without checkpointer
- [LLM Providers](/openwiki/components/llm-providers.md) — API keys needed
- [Database](/openwiki/components/database.md) — DATABASE_URL needed
- [OpenWiki Automation](/openwiki/openwiki-automation.md) — CI/CD secrets
- [Testing](/openwiki/testing.md) — Test environment setup