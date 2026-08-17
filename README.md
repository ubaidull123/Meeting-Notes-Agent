# step-by-step-instructions.md

**Project:** Meeting Notes → Action Items — AI Agent
**Difficulty:** Intermediate
**Estimated duration (guideline):** 3–4 weeks
**Goal:** Build a single autonomous agent (CLI/desktop process) that ingests a meeting audio/transcript and produces: cleaned transcript, structured summary, decisions, action items (with assignees/deadlines/priorities), creates tasks in a PM tool, and sends follow-up emails — pausing only where explicit human approval is required.

---

# Overview — one-sentence plan

Implement a linear agent pipeline: **Validate input → (Transcribe) → Clean transcript → Summarize → Extract decisions → Extract action items → Redact sensitive data → Pause for human review → Create PM tasks → Draft email → Pause for email approval → Send email → Persist meeting record**.

---

# 1. Project layout (suggested repository)

```
meeting-agent/
├─ README.md
├─ pyproject.toml / requirements.txt
├─ src/
│  ├─ main.py
│  ├─ agent/
│  │  ├─ pipeline.py
│  │  ├─ transcription.py
│  │  ├─ cleaning.py
│  │  ├─ summarization.py
│  │  ├─ extraction.py
│  │  ├─ redaction.py
│  │  ├─ pm_integration.py
│  │  ├─ emailer.py
│  │  └─ storage.py
│  ├─ models.py
│  └─ prompts/
│     ├─ summarize_prompt.txt
│     ├─ extract_decisions_prompt.txt
│     └─ extract_actions_prompt.txt
├─ samples/
│  ├─ sample_meeting.mp3
│  └─ sample_transcript.json
└─ docs/
   └─ run_instructions.md
```

---

# 2. Tech stack recommendations

* **Language:** Python 3.11+
* **Data models:** Pydantic (or dataclasses + TypedDicts)
* **Speech-to-text:** Whisper (local) or cloud STT (OpenAI/Google) — prefer diarization-capable solution (whisperx, pyannote)
* **LLM:** OpenAI GPT family (or equivalent) for summarization/extraction; use low temperature and structured JSON outputs
* **PM tool:** Trello, Asana, Jira, or ClickUp (example adapters provided for Trello/Asana)
* **Email:** SMTP or API (SendGrid/Mailgun) — prefer API for delivery logs
* **Storage:** Prototype: JSON files per meeting; Production: SQLite or cloud DB
* **Utilities:** Tenacity for retries, structured JSON logging

---

# 3. Data models (implement in `models.py`)

Use Pydantic models for validation and serialization.

```py
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum
from uuid import uuid4

class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class Attendee(BaseModel):
    name: str
    email: EmailStr

class ActionItem(BaseModel):
    id: Optional[str] = None
    description: str
    assignee_email: Optional[EmailStr]
    deadline: Optional[datetime]
    priority: Priority
    context_quote: str

class Decision(BaseModel):
    id: Optional[str] = None
    summary: str
    participants: List[str]
    context_quote: str

class Meeting(BaseModel):
    id: Optional[str] = None
    title: str
    date: datetime
    attendees: List[Attendee]
    audio_file_path: Optional[str]
    project_name: Optional[str]
    raw_transcript_path: Optional[str]
    cleaned_transcript_path: Optional[str]
    summary_text: Optional[str]
    decisions: List[Decision] = []
    action_items: List[ActionItem] = []
    pm_task_ids: List[str] = []
    sent_email_id: Optional[str]
```

Assign `id = str(uuid4())` at creation.

---

# 4. High-level pipeline (`pipeline.py`)

1. Validate input (file exists, metadata present).
2. Transcribe audio (if provided) — produce speaker turns with timestamps.
3. Clean transcript (remove fillers, merge turns, keep start timestamps).
4. Produce meeting summary (2–3 paragraphs + topics).
5. Extract decisions (explicit agreements only).
6. Extract action items (task, assignee, deadline, priority, context quote).
7. Redact sensitive info (salary, phones, health, extra PII).
8. Pause for human review (user can edit/add/delete/approve).
9. Create PM tasks for approved actions (handle retries and failures).
10. Draft follow-up email (personalized per attendee).
11. Pause for email approval (user edits).
12. Send the email (with retries).
13. Save meeting record (full audit data).

Implement a `run(meeting_metadata, audio_or_transcript)` that persists state after each major step so it can resume.

---

# 5. Detailed implementation notes by step

## Step 1 — Input validation

* Verify `title`, `date`, `attendees` (names + valid emails).
* Confirm audio path exists or transcript is parsable.
* Create initial `Meeting` record with generated `id`.

Checklist:

* [ ] file exists (if audio)
* [ ] attendees list non-empty
* [ ] meeting date parseable

## Step 2 — Transcription

* If transcript provided, normalize it (speaker labels + timestamps if present).
* If audio provided:

  * Use STT with diarization (whisperx, pyannote, or cloud diarization).
  * Output: list of turns: `{ speaker_id, start_time, end_time, text }`.
  * Save raw transcript JSON.

Notes:

* Chunk large files >1 hour and stitch transcripts with timestamps.

## Step 3 — Cleaning transcript

* Remove filler tokens (`um`, `uh`, `you know`, `like`) via regex while preserving meaning.
* Merge consecutive turns from same `speaker_id` if gap < threshold (e.g., 3s).
* Keep a start timestamp for each speaker turn.
* Attempt speaker → attendee mapping using explicit mentions ("I'm X", "X here") or addressing ("Ubaidi, can you..."). If mapping fails, keep `Speaker 1` labels for review.

Save cleaned transcript.

## Step 4 — Summarization

* Prompt LLM to output structured JSON:

```json
{
  "summary": "Two to three paragraph text...",
  "topics": ["topic1", "topic2"]
}
```

* Keep temperature low; chunk transcript when necessary.

## Step 5 — Extract decisions

* Return JSON array of decisions:

  * `summary`, `participants` (attendee names if mappable), `context_quote`, `timestamp`.
* Include only **explicit** decisions (no casual suggestions).

## Step 6 — Extract action items

* Return JSON list of `ActionItem` objects with:

  * `description`, `assignee_name/email` (or `null` if ambiguous), `deadline` (YYYY-MM-DD or `null`), `priority` (high|medium|low), `context_quote`, `timestamp`.
* Conversion rules:

  * Map relative dates (e.g., "by Friday") to absolute dates using meeting date if unambiguous; otherwise `null`.
  * Priority: `urgent/ASAP/today` → `high`; `next week/soon` → `medium`; otherwise `low`.
* Do **not** guess assignee if ambiguous — mark unassigned.

## Step 7 — Redaction

* Regex + heuristics to redact:

  * Salaries / compensation (currency + numbers)
  * Phone numbers
  * Health information (sensitive personal health details)
  * Personal identifiers beyond name and work email
* Replace with `[REDACTED]` and log redactions.

## Step 8 — Pause for human review (mandatory)

* Present cleaned transcript, summary, decisions, and action items in an editable UI (CLI or small web UI).
* User actions allowed:

  * Approve all
  * Edit any action item (assignee, deadline, description, priority)
  * Add action items
  * Delete incorrect action items
* Persist edits; require explicit `APPROVE` to continue.

## Step 9 — Create tasks in PM tool

* For each approved action:

  * Map `assignee_email` → PM user id; if not found, create unassigned task or add an assignment comment.
  * Create task with description, due date, labels (meeting-title, meeting-date), and link to meeting record.
  * Retry with exponential backoff on transient failures (max attempts 3).
  * Log failed tasks and continue.

## Step 10 — Draft follow-up email

* Components:

  * Greeting
  * 2–3 paragraph meeting summary
  * Bulleted decisions
  * Per-attendee list of assigned tasks with PM links
  * Closing + link to full meeting record
* Produce both plaintext and HTML drafts. Present draft to user for edit.

## Step 11 — Pause for email approval

* Show draft (preview with links). Allow edits. Wait for explicit approval.

## Step 12 — Send the email

* Send via configured SMTP/API. Retry transient failures (max 3).
* Log delivery status and message id.

## Step 13 — Save meeting record

* Atomic save of:

  * metadata, cleaned transcript, summary, decisions, action items, PM task ids, email draft + sent status, redaction log.
* Storage options:

  * prototype: `records/{meeting_id}.json`
  * production: SQLite or cloud DB with attachments table.

---

# 6. Integration details (PM tool & Email)

### PM integration (`pm_integration.py`)

Adapter interface:

```py
class PMClient:
    def create_task(self, project_name, title, description, assignee_email, due_date, labels) -> str: ...
    def find_user_by_email(self, email) -> Optional[str]: ...
```

Implement `TrelloClient` or `AsanaClient` that adheres to this interface. Include rate-limit handling and retries.

### Emailer (`emailer.py`)

Interface:

```py
class EmailClient:
    def draft_email(self, from_email, to_emails, subject, plaintext, html) -> str  # returns draft_id
    def send_email(self, draft_id) -> dict  # returns { success: bool, message_id: str, error: ... }
```

If using SMTP, implement `send` with TLS and proper headers. For APIs, use their client libraries and return the message id.

---

# 7. LLM prompt templates (keep in `prompts/`)

Design prompts that demand structured JSON. Example `extract_actions_prompt.txt`:

```
You are a strict extractor. Input: a cleaned meeting transcript with speaker turns and timestamps.

Return JSON array "action_items" with objects:
{
  "description": "...",
  "assignee_name": "... or null",
  "assignee_email": "... or null",
  "deadline": "YYYY-MM-DD or null",
  "priority": "high|medium|low",
  "context_quote": "... exact quote ...",
  "timestamp": "HH:MM:SS"
}

Rules:
- Only include tasks that were actually assigned.
- If assignee is ambiguous, set assignee_name/email to null and add "ambiguous": true.
- Normalize dates relative to meeting date when phrases like "next Friday" appear; if unclear, set null.
- Do not invent facts.
```

Validate every LLM response against your schema. If it fails parsing, retry with clarified instruction and the prior output included.

---

# 8. Testing & validation plan

* **Unit tests:** transcript cleaning, date normalization, redaction, Pydantic validation.
* **Integration tests:** end-to-end run with mocked PM & Email clients; simulate human approvals.
* **Acceptance criteria:**

  * Cleaned transcript saved and readable.
  * Summary produced covering main topics.
  * Explicit decisions extracted.
  * Action items assigned only when explicit.
  * PM tasks created with meeting labels and links.
  * Follow-up email includes personalized task lists.
  * Sensitive fields redacted before storage and sending.

---

# 9. UX for human approvals (minimum viable)

* **CLI:** fast to implement. Print sections and prompt per action item: `[A]pprove [E]dit [D]elete [M]ark Unassigned`. Persist state to JSON.
* **Local web UI:** Flask/FastAPI + minimal HTML form for inline edits and a final "Approve and continue" button.
* **Requirement:** The agent must never proceed without explicit user approval.

---

# 10. Error handling and retries

* Wrap external calls (STT, LLM, PM API, Email API) with retry/backoff (use `tenacity`).
* Distinguish transient vs permanent failures; for permanent failures, abort with a clear human-readable error and remediation steps.
* Log errors with meeting id for traceability.

---

# 11. Security & privacy

* Encrypt meeting records at rest if containing sensitive content (AES or platform-managed encryption).
* Keep API keys in environment variables or a secrets manager.
* Provide a transcript retention policy (configurable) — default: delete raw audio after X days.
* Redaction is heuristic; require human review as final safeguard.

---

# 12. Deployment & run instructions (prototype)

1. Create virtualenv, install deps: `pip install -r requirements.txt`
2. Set environment variables: `OPENAI_API_KEY`, `PM_API_KEY`, `EMAIL_API_KEY`, `SMTP_*`
3. Run:

```bash
python -m src.main \
  --audio samples/sample_meeting.mp3 \
  --title "Weekly Sync" \
  --date "2026-08-01T10:00:00" \
  --attendees attendees.json
```

4. Follow console or web UI prompts to review and approve extracted items and email drafts.

Include `docs/run_instructions.md` with concrete examples and environment setups.

---

# 13. Example outputs — JSON schema for final meeting record

```json
{
  "id": "uuid",
  "title": "Weekly Sync",
  "date": "2026-08-01T10:00:00Z",
  "attendees": [{"name":"Ubaidi","email":"ubaidi@example.com"}],
  "cleaned_transcript_path":"records/uuid_transcript.txt",
  "summary":"Two paragraphs ...",
  "topics":["roadmap","migration","qa"],
  "decisions":[
    {"id":"d1","summary":"Migrate to Postgres by end of Q3","participants":["Alice","Bob"],"context_quote":"..."}
  ],
  "action_items":[
    {"id":"a1","description":"Migrate DB","assignee_email":"alice@example.com","deadline":"2026-09-30T00:00:00Z","priority":"high","context_quote":"..."}
  ],
  "pm_task_ids":["trello:cardid123"],
  "sent_email_id":"email:msgid678",
  "redaction_log":[{"field":"summary","original":"Salary 100k","redacted":"[REDACTED]"}]
}
```

---

# 14. Acceptance & evaluation checklist (final handoff)

* [ ] Agent completes the full pipeline and pauses at Step 8 and Step 11.
* [ ] Human review UI works and edits persist.
* [ ] For 10 sample meetings: >90% of explicit action items detected and correctly assigned (manual check).
* [ ] PM tool tasks created with links and labels.
* [ ] Emails delivered (or simulated) and include personalized task lists.
* [ ] Redaction removes prohibited info from stored and outgoing artifacts.

---

# 15. Suggested milestones (3–4 week split)

* **Week 1:** Project skeleton, models, transcription & basic cleaning; save transcripts.
* **Week 2:** LLM summarization and extraction prompts; iterate on prompt reliability. Implement redaction heuristics.
* **Week 3:** PM & Email adapters + pause/approval UI; end-to-end with mocks.
* **Week 4:** Integration testing, error handling, logging, and polish. Run acceptance tests.

---

# 16. Deliverables for intern submission

* Source code with unit & integration tests.
* `samples/` with ≥3 meeting example inputs + outputs (cleaned transcripts, JSON records).
* `docs/` with run instructions and architecture notes.
* Short demo (video or text walkthrough) showing: upload → review edits → create tasks → send email.
* README explaining configuration and where to plug API keys.

---

# Final notes / development tips

* Keep the full transcript and exact context quotes for explainability and auditability.
* Prefer non-destructive edits: keep original raw transcript; store edited artifacts separately.
* Validate LLM outputs against a schema; if validation fails, retry with clearer prompts and include the previous failed output for context.
* For speaker→attendee mapping, use conservative heuristics and rely on human review to correct mappings.
* The human approval pauses are the safety checks — implement them robustly.

---

If you want, I can convert this markdown into a downloadable file, or generate `models.py` and `pipeline.py` skeletons next. Which do you prefer?
