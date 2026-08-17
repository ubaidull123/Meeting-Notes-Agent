┌─────────────────────────────────────────────────────────────────┐
│                         USER (CLI)                              │
│  Provides: audio file + metadata (title, date, attendees)       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT (LangGraph StateGraph)                  │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │  Input   │──▶│Transcribe│──▶│  Clean   │──▶│ Summarize│    │
│  │  Valid.  │   │  Audio   │   │Transcript│   │ Meeting  │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│                                                       │         │
│                                                       ▼         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐      │
│  │  Save    │◀──│  Send    │◀──│  Email   │◀──│  Create │      |
│  │ Record   │   │  Email   │   │  Approve │   │  Tasks   │      │
│  └──────────┘   └──────────┘   │ (Pause)   │   │          │     │
│                     ▲          └──────────┘   └──────────┘      │
│                     │                ▲                ▲         │
│                     │           ┌────┴────────┐       │         │
│                     │           │  Action     │       │         │
│                     │           │  Items      │───────┘         │
│                     │           │  Approve    │                 │
│                     │           │  (Pause)    │                 │
│                     │           └────▲────────┘                 │
│                     │                │                          │
│                     │           ┌────┴────────┐                 │
│                     │           │  Redact     │                 │
│                     │           │  Sensitive  │                 │
│                     │           │  Info       │                 │
│                     │           └────▲────────┘                 │
│                     │                │                          │
│                     │           ┌────┴────────┐                 │
│                     │           │  Action     │                 │
│                     │           │  Items      │                 │
│                     │           └────▲────────┘                 │
│                     │                │                          │
│                     │           ┌────┴────────┐                 │
│                     │           │  Decisions  │                 │
│                     │           └────▲────────┘                 │
│                     │                │                          │
│                  (Human-In-The-Loop Checkpoints)                │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              External Services (Real or Mocked)                 │
│   Whisper/AssemblyAI  •  Trello/Notion  •  Gmail/SendGrid       │
└─────────────────────────────────────────────────────────────────┘

meeting-agent/
├── README.md
├── pyproject.toml
├── .env.example
├── .env
│
├── data/
│   ├── input/                    # audio files dropped here
│   ├── transcripts/              # cached cleaned transcripts
│   ├── mock_trello.json          # mock tasks (when not using real Trello)
│   ├── mock_emails/              # mock sent emails
│   └── meetings.db               # SQLite database
│
├── src/
│   ├── __init__.py
│   ├── main.py                   # CLI entrypoint
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── meeting.py            # Meeting, Attendee
│   │   ├── summary.py            # MeetingSummary, Decision, ActionItem
│   │   ├── transcript.py         # TranscriptSegment, CleanedTranscript
│   │   └── state.py              # AgentState (LangGraph state TypedDict)
│   │
│   ├── steps/                    # one file per step in the spec
│   │   ├── __init__.py
│   │   ├── step01_input.py
│   │   ├── step02_transcribe.py
│   │   ├── step03_clean.py
│   │   ├── step04_summarize.py
│   │   ├── step05_decisions.py
│   │   ├── step06_action_items.py
│   │   ├── step07_redact.py
│   │   ├── step08_review.py
│   │   ├── step09_create_tasks.py
│   │   ├── step10_draft_email.py
│   │   ├── step11_email_review.py
│   │   ├── step12_send_email.py
│   │   └── step13_save.py
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── base.py               # abstract TaskClient, EmailClient
│   │   ├── mock_task_client.py
│   │   ├── mock_email_client.py
│   │   ├── trello_client.py
│   │   └── gmail_client.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py             # configured LLM client
│   │   └── prompts/
│   │       ├── summarize.txt
│   │       ├── extract_decisions.txt
│   │       ├── extract_action_items.txt
│   │       ├── map_speakers.txt
│   │       ├── redact.txt
│   │       └── draft_email.txt
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── review_items.py       # action items review UI
│   │   └── review_email.py       # email review UI
│   │
│   ├── graph.py                  # builds the LangGraph StateGraph
│   ├── storage.py                # SQLite persistence
│   └── utils.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_redaction.py
│   ├── test_cleaning.py
│   ├── test_prompts.py
│   ├── test_integrations.py
│   └── fixtures/
│       ├── sample_transcript.txt
│       ├── sample_dirty_transcript.txt
│       └── sample_with_pii.txt
│
└── scripts/
    ├── run_demo.py               # full end-to-end demo
    ├── inspect_state.py          # debug a meeting in progress
    └── query_past_meetings.py    # search saved meetings
