# Meeting Notes Agent

A LangGraph-based meeting processing pipeline that transforms raw meeting transcripts or audio recordings into structured, actionable meeting notes with human-in-the-loop review checkpoints.

## Architecture Overview

```
┌─────────────┐
│   INPUT     │  ← Meeting metadata + transcript/audio
└──────┬──────┘
       ▼
┌─────────────┐
│ TRANSCRIBE  │  ← Whisper (local) or OpenAI API (audio → text)
└──────┬──────┘
       ▼
┌─────────────┐
│   CLEAN     │  ← Remove filler words, fix formatting
└──────┬──────┘
       ▼
┌─────────────┐
│  SUMMARIZE  │  ← LLM generates summary, decisions, action items
└──────┬──────┘
       ▼
┌─────────────┐
│  REDACT     │  ← Remove PII, confidential info
└──────┬──────┘
       ▼
┌─────────────┐     ┌──────────────────┐
│ HUMAN REVIEW│────▶│  APPROVE / REJECT│  ← Checkpoint 1
└──────┬──────┘     └──────────────────┘
       │
       ▼ (if approved)
┌─────────────┐
│  PM TASKS   │  ← Create structured task records
└──────┬──────┘
       ▼
┌─────────────┐
│ DRAFT EMAIL │  ← Generate follow-up email
└──────┬──────┘
       ▼
┌─────────────┐     ┌──────────────────┐
│ EMAIL REVIEW│────▶│  APPROVE / REJECT│  ← Checkpoint 2
└──────┬──────┘     └──────────────────┘
       │
       ▼ (if approved)
┌─────────────┐
│  SEND EMAIL │  ← Resend API
└──────┬──────┘
       ▼
┌─────────────┐
│   STORE     │  ← PostgreSQL persistence
└─────────────┘
```

## Project Structure

```
src/meeting_notes_agent/
├── main.py                    # CLI entry point
├── graph.py                   # LangGraph workflow definition
├── state_schema.py            # Pydantic state model (single source of truth)
├── observability.py           # LangSmith tracing configuration
├── database/
│   ├── __init__.py
│   └── postgresdb.py          # PostgreSQL connection pool, checkpointer, schema
├── Nodes/                     # Pipeline nodes (one per processing step)
│   ├── i_Input.py             # Input validation & quota checking
│   ├── ii_transcribe_audio.py # Audio transcription (Whisper/OpenAI)
│   ├── iii_clean_transcript.py# Transcript cleaning
│   ├── iv_summerize.py        # LLM summarization & extraction
│   ├── v_extraction.py        # Decision/action item extraction
│   ├── vi_redaction.py        # PII/confidential redaction
│   ├── vii_PM_tasks.py        # Task record creation
│   ├── viii_emailing.py       # Email draft generation
│   ├── v_human_review.py      # Human review checkpoint 1 (after redaction)
│   ├── send_email.py          # Email sending via Resend
│   └── ix_store.py            # Database persistence
├── llms/
│   ├── API_Based/             # Cloud LLM providers
│   │   ├── openai.py
│   │   ├── groq.py
│   │   └── openrouter.py
│   ├── Local/                 # Local models
│   │   └── hf/whisper.py      # Local Whisper transcription
│   └── prompts/               # Prompt templates
│       ├── summarize_prompt.py
│       ├── redaction_prompt.py
│       └── extract_decisions_prompt.py
├── models/
│   └── task.py                # Task data models
├── storage/
│   └── task_storage.py        # Local task file storage
└── utils/
    ├── email_utils.py         # Email formatting helpers
    └── retry.py               # Retry logic with exponential backoff
```

## Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL database
- OpenAI API key (for LLM processing)
- Resend API key (for email sending)

### Installation

```powershell
# Clone and navigate
cd meeting-notes-agent

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .

# Or with uv (faster)
uv sync
```

### Configuration

Create `.env` file from template:

```powershell
copy .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
# Email: choose one provider
EMAIL_PROVIDER=mailgun
MAILGUN_API_KEY=your-new-mailgun-key
MAILGUN_DOMAIN=your-mailgun-domain
MAILGUN_BASE_URL=https://api.mailgun.net
MAILGUN_FROM_EMAIL=Meeting Notes <postmaster@your-mailgun-domain>
DATABASE_URL=postgresql://user:pass@localhost:5432/meeting_notes

# Optional: LangSmith tracing
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=meeting-notes-agent
```

### Initialize Database

```powershell
# Run once to create tables
.\.venv\Scripts\python.exe -c "from meeting_notes_agent.database.postgresdb import init_db; init_db(); print('Database initialized')"
```

## Usage

### CLI Commands

```powershell
# Show help
meeting-notes-agent --help
# or
.\.venv\Scripts\python.exe -m meeting_notes_agent.main --help
```

#### 1. Process Transcript Text (Fastest)

```powershell
meeting-notes-agent `
  --transcript-text "Speaker 1: We decided to launch in October. Action: John to prepare checklist by Friday." `
  --attendees "John Doe:john@company.com,Jane Smith:jane@company.com" `
  --meeting-title "Launch Planning" `
  --meeting-date 2026-08-20
```

#### 2. Process Audio File

```powershell
meeting-notes-agent `
  --audio-file "data/uploads/meeting.mp3" `
  --attendees "John Doe:john@company.com" `
  --meeting-title "Team Sync"
```

#### 3. Process Transcript File

```powershell
meeting-notes-agent `
  --transcript-file "transcripts/meeting.txt" `
  --attendees "John Doe:john@company.com"
```

#### 4. Load from JSON File

Create `input.json`:
```json
{
  "meeting_title": "Q3 Planning",
  "meeting_date": "2026-08-20",
  "meeting_time": "10:00",
  "project_name": "Product",
  "transcript_text": "Speaker 1: ...",
  "attendees": [
    {"name": "John Doe", "email": "john@company.com"},
    {"name": "Jane Smith", "email": "jane@company.com"}
  ],
  "agenda": ["Review Q2", "Plan Q3"],
  "notes": "Quarterly planning"
}
```

Run:
```powershell
meeting-notes-agent --input-file input.json
```

#### 5. Interactive Mode

```powershell
meeting-notes-agent --interactive
```

#### 6. Output Options

```powershell
# Quiet mode (summary + action items only)
meeting-notes-agent --transcript-text "..." --attendees "..." --quiet

# Save full state to JSON
meeting-notes-agent --transcript-text "..." --attendees "..." --output-json result.json
```

## Human-in-the-Loop Review

The workflow pauses at **two review checkpoints**:

### Checkpoint 1: After Redaction
- Shows redacted summary, decisions, action items
- Options: **Approve** → continue, **Reject with instructions** → re-summarize, **Reject** → stop

### Checkpoint 2: After Email Draft
- Shows generated follow-up email
- Options: **Approve & Send** → send email + store, **Reject with instructions** → redraft, **Reject** → stop

### Resuming a Paused Workflow

Workflows are checkpointed in PostgreSQL with a `thread_id`. To resume:

```python
# Using the same thread_id from the original run
config = {"configurable": {"thread_id": "your-thread-id-here"}}
result = graph.invoke({"human_review_decision": "approve"}, config=config)
```

Or via LangGraph Studio (see below).

## LangGraph Studio (Visual Debugging)

```powershell
# Start the dev server
.\scripts\run-langgraph.ps1
```

Opens: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

Features:
- Visual graph execution
- Step-through debugging
- State inspection at each node
- Resume interrupted runs
- Run history

## State Schema

All data flows through a single `MeetingState` Pydantic model (`state_schema.py`):

```python
class MeetingState(BaseModel):
    # Identification
    meeting_id: str
    meeting_title: str
    meeting_date: date
    meeting_time: Optional[str]
    project_name: Optional[str]
    user_id: Optional[int]

    # Input (exactly one required)
    audio_file_path: Optional[str]
    transcript_file_path: Optional[str]
    transcript_text: Optional[str]

    # Attendees & context
    attendees: List[Attendee]
    agenda: List[str]
    notes: Optional[str]

    # Pipeline outputs
    raw_transcription: Optional[str]
    cleaned_transcription: Optional[str]
    summary: Optional[str]
    decisions: List[str]
    action_items: List[str]

    # Redacted outputs
    redacted_transcription: Optional[str]
    redacted_summary: Optional[str]
    redacted_decisions: List[str]
    redacted_action_items: List[str]

    # Email
    email_draft: Optional[str]
    email_sent: bool
    email_response: Optional[dict]

    # Tasks
    pm_tasks: List[Task]
    task_collection: Optional[TaskCollection]

    # Storage
    stored: bool
    storage_error: Optional[str]

    # Human review
    human_review_decision: Optional[str]
    human_review_instructions: Optional[str]
    email_review_decision: Optional[str]
    email_review_instructions: Optional[str]

    # Tracking
    tokens_used_accrued: int
```

## Database Schema

PostgreSQL tables created by `init_db()`:

| Table | Purpose |
|-------|---------|
| `users` | Authentication (legacy, not used in CLI) |
| `meetings` | Core meeting records with all pipeline outputs |
| `attendees` | Meeting attendees (linked to meetings) |
| `tasks` | PM task records extracted from meetings |
| `user_quotas` | Monthly meeting limits & credits |
| `user_credits` | Current credit balance |
| `user_usage` | Monthly usage rollup |

LangGraph checkpoints are stored in `checkpoints` table (managed by `PostgresSaver`).

## LLM Providers

Configure in `.env` or code:

| Provider | Models | Use Case |
|----------|--------|----------|
| OpenAI | gpt-4o, gpt-4o-mini | Default, best quality |
| Groq | llama-3.1-70b, mixtral | Fast, cost-effective |
| OpenRouter | 100+ models | Model variety |
| Local (HF) | whisper-large-v3 | Offline transcription |

Default: **OpenAI** for chat and audio transcription, configurable through environment variables.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM |
| `OPENAI_CHAT_MODEL` | No | Chat model (default: `gpt-4o-mini`) |
| `OPENAI_TRANSCRIPTION_MODEL` | No | Audio transcription model (default: `gpt-4o-mini-transcribe`) |
| `OPENAI_TIMEOUT_SECONDS` | No | Per-request timeout in seconds (default: `60`) |
| `EMAIL_PROVIDER` | Yes | `mailgun` (recommended) or `resend` |
| `MAILGUN_API_KEY` | When using Mailgun | Mailgun private API key |
| `MAILGUN_DOMAIN` | When using Mailgun | Sending domain, including sandbox domains |
| `MAILGUN_BASE_URL` | No | Mailgun API base URL (default: `https://api.mailgun.net`) |
| `MAILGUN_FROM_EMAIL` | No | Sender; defaults to the domain's `postmaster` address |
| `RESEND_API_KEY` | When using Resend | Resend API key for the alternative provider |
| `RESEND_FROM_EMAIL` | When using Resend | Verified sender email |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `POSTGRES_USER` | No* | DB user (if not in DATABASE_URL) |
| `POSTGRES_PASSWORD` | No* | DB password |
| `POSTGRES_HOST` | No* | DB host (default: localhost) |
| `POSTGRES_PORT` | No* | DB port (default: 5432) |
| `POSTGRES_DB` | No* | DB name (default: meeting_notes) |
| `LANGSMITH_API_KEY` | No | LangSmith tracing |
| `LANGSMITH_TRACING` | No | Enable tracing (true/false) |
| `LANGSMITH_PROJECT` | No | Project name in LangSmith |

*Used to construct DATABASE_URL if not provided directly.

## Development

### Run Tests

```powershell
# No formal tests yet - run manually
.\.venv\Scripts\python.exe -m meeting_notes_agent.main --interactive
```

### Add a New Node

1. Create `src/meeting_notes_agent/Nodes/new_node.py`
2. Define function accepting `state: MeetingState` → `dict`
3. Add to `graph.py`: `graph.add_node("NewNode", new_node_fn)`
4. Add edges: `graph.add_edge("PreviousNode", "NewNode")`

### Prompt Engineering

Prompts are in `llms/prompts/`. Each is a Python string template with `{variable}` placeholders.

Example (`summarize_prompt.py`):
```python
SUMMARIZE_PROMPT = """
You are an expert meeting summarizer. Analyze this transcript:

{transcript}

Provide:
1. Summary (2-3 paragraphs)
2. Key decisions (bullet list)
3. Action items (bullet list with owners)
"""
```

## Troubleshooting

### "Checkpointer requires thread_id"
Always provide a `thread_id` in config when invoking the graph:
```python
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = graph.invoke(state, config=config)
```

### "DATABASE_URL not set"
Ensure `.env` has valid PostgreSQL connection string.

### "No module named 'meeting_notes_agent'"
Install in editable mode: `pip install -e .` or `uv sync`

### Audio transcription fails
- Ensure ffmpeg is installed (required for audio processing)
- Check file format: MP3, WAV, M4A only
- File size limit: ~100 MB

### Email not sending
- For Mailgun, verify `EMAIL_PROVIDER=mailgun`, `MAILGUN_API_KEY`, and `MAILGUN_DOMAIN`.
- A Mailgun sandbox can send only to recipients you have authorized in Mailgun.
- For Resend, verify `RESEND_API_KEY` and `RESEND_FROM_EMAIL`; its onboarding sender only delivers to the account owner.

## License

MIT License - See LICENSE file for details.
