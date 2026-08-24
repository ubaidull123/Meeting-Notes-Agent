---
type: planning
title: Wiki Skeleton - Meeting Notes Agent
description: Planned documentation structure for the Meeting Notes Agent repository wiki
tags: [planning, skeleton, architecture]
---

# Wiki Skeleton - Meeting Notes Agent

## Overview

This document tracks the planned wiki structure for the Meeting Notes Agent repository. The wiki will be organized by system/domain rather than by file structure.

## Planned Wiki Structure

### 1. `/openwiki/quickstart.md` (entrypoint)
- High-level architecture map
- Links to all major concept pages
- Task-routing table from change intent to relevant pages
- Validation commands

### 2. `/openwiki/architecture/`
- `overview.md` - System architecture, pipeline flow diagram, data flow
- `state-schema.md` - MeetingState Pydantic model, field descriptions, validation rules
- `graph-definition.md` - LangGraph workflow definition, nodes, edges, conditional routing

### 3. `/openwiki/pipeline/`
- `overview.md` - Pipeline stages overview, inputs/outputs
- `input-validation.md` - Input node, quota checking, source validation
- `transcription.md` - Audio transcription (Whisper/OpenAI), chunking, providers, FFmpeg dependency, 25MB limit, mono 16kHz/64kbps re-encoding
- `cleaning.md` - Transcript cleaning LLM node, filler word removal, formatting
- `summarization.md` - Summary generation, decisions extraction, action items, rewrite support
- `extraction.md` - Decision/action item extraction node
- `redaction.md` - PII/confidential redaction, delimiter parsing, Markdown fallback, repair logic, "none" filtering
- `human-review.md` - First checkpoint: interrupt() mechanism, review payload, Command resume, checkpoint durability, routing logic
- `pm-tasks.md` - Task creation from action items, dual persistence (database + local JSON files in data/tasks/), TaskCollection serialization
- `email-drafting.md` - Email generation from redacted content, rewrite support
- `email-review.md` - Second checkpoint: interrupt() mechanism, email draft review, Command resume, routing logic
- `email-sending.md` - Dual-provider email utility (Mailgun/Resend), retry policy (3 attempts, exponential backoff + jitter), Resend test domain validation, sender resolution, EmailDeliveryError
- `storage.md` - Database persistence, checkpoint recovery, completion marking, local task file storage

### 4. `/openwiki/api/`
- `overview.md` - FastAPI app structure, CORS, rate limiting, exception handling
- `auth.md` - JWT HS256 access/refresh tokens (30min/7days), bcrypt, get_current_user_id dependency, require_admin guard, token rotation
- `meetings.md` - Meeting CRUD, audio/transcript upload, processing queue, status
- `review-endpoints.md` - Human review endpoints (get content, submit decision)
- `email-review-endpoints.md` - Email review endpoints
- `tasks.md` - Task CRUD, listing, status updates
- `settings.md` - User AI settings, email settings, API key management, meeting overrides, credits/transactions/usage
- `admin.md` - Admin endpoints for user/meeting management

### 5. `/openwiki/services/`
- `overview.md` - Service layer architecture, ProcessingService as orchestrator
- `processing-service.md` - Core service: state mapping, checkpoint persistence, quota/credits, background jobs (BackgroundTasks, process_meeting_in_background, thread_id continuity, isolated DB sessions), credit reservation/deduction flow, pricing rules, pricing rules per provider/model/service
- `ai-settings.md` - User AI config (LLM provider/model), transcription settings, BYOK credentials, meeting-level overrides, email sender configuration
- `credits-billing.md` - Credits system, monthly quotas, credit deduction tracking, usage recording per meeting/service/provider/model, CreditTransaction ledger, monthly quota enforcement (meetings + credits), admin credit adjustment
- `email-settings.md` - Sender email resolution, verification, dual-provider config (Resend/SMTP), override merging
- `meeting-overrides.md` - Per-meeting AI config overrides

### 6. `/openwiki/database/`
- `overview.md` - SQLAlchemy models, PostgreSQL schema, relationships
- `models.md` - User, Meeting, Attendee, Task, Quota, Credits, Usage, AIConfig, Credentials, EmailConfig, Overrides, PricingRules, CreditTransaction, UsageRecord models
- `repositories.md` - Repository pattern implementations for User, Meeting, Attendee, Task, Quota, Credits, Usage
- `checkpointing.md` - LangGraph checkpointer: JsonPlusSerializer with Attendee registration, three-tier selection (LangGraph API → SQLite → Postgres), cancellable_node wrapper (cooperative cancellation via MeetingStatus.CANCELLED), thread_id persistence on Meeting, recovery on process restart

### 7. `/openwiki/llm/`
- `overview.md` - LLM provider abstraction, runtime resolution
- `providers.md` - PROVIDER_CATALOG structure, capability-based filtering, model metadata (tier/speed/quality/recommended_for), model validation, disabled providers for future expansion
- `prompts.md` - Prompt templates (summarize, redaction, extraction)
- `retry-logic.md` - Tenacity retry decorators, retryable error classification
- `credential-encryption.md` - AES-GCM encryption, HKDF key derivation, BYOK support, encrypt_json, mask_key

### 8. `/openwiki/frontend/`
- `overview.md` - React + Vite + Tailwind structure, routing, auth context
- `pages.md` - Dashboard, Meetings, CreateMeeting, MeetingReview pages
- `components.md` - UI components (modals, timeline, badges, forms)
- `review-flow.md` - Status-driven routing (AWAITING_REVIEW → HumanReviewModal, AWAITING_EMAIL_REVIEW → EmailReviewModal), TanStack Query for review content, mutations for resumeProcessing/resumeEmailReview, toast notifications

### 9. `/openwiki/testing/`
- `overview.md` - Test structure, fixtures, database sessions
- `meeting-tests.md` - Meeting CRUD, upload, processing tests
- `review-flow-tests.md` - Checkpoint persistence, resume, rejection tests, survive-process-restart
- `auth-admin-tests.md` - Authentication, admin endpoints tests
- `credential-encryption-tests.md` - AES-GCM encryption/decryption tests

### 10. `/openwiki/deployment/`
- `overview.md` - Environment variables, Docker, database initialization
- `configuration.md` - Settings management, .env.example reference

### 11. `/openwiki/extension-points.md`
- Adding new LLM providers (provider catalog, validation, runtime resolution)
- Adding new pipeline nodes (graph registration, state schema updates)
- Custom prompt templates (prompts/ directory, prompt loading)
- Extending state schema (MeetingState, Attendee, model validators)
- Credential encryption and BYOK support (encryption service, provider config)
- Email provider configuration (Resend/SMTP, sender resolution)
- Meeting AI overrides (per-meeting config, override service)

### 12. `/openwiki/backlog.md`
- Known gaps, future work items

## Evidence Coverage Status

- [x] Core pipeline graph (`graph.py`)
- [x] Universal state schema (`state_schema.py`)
- [x] CLI entry point (`main.py`)
- [x] All 12 pipeline nodes (`Nodes/`)
- [x] PostgreSQL database layer (`database/`)
- [x] FastAPI API layer (`api/`)
- [x] Service layer (`services/`)
- [x] LLM providers & prompts (`llms/`)
- [x] Frontend React app (`frontend/`)
- [x] Test suites (`tests/`)
- [x] Utility modules (`utils/`)
- [x] Task models (`models/`)
- [x] AI settings & credential management (`config/providers.py`, `services/ai_settings_service.py`, `services/credential_encryption.py`)
- [x] Database models for AI config, credentials, billing (`database/models_ai_config.py`)
- [x] Repository pattern (`database/repositories.py`)
- [x] Email sending workflow (`services/email_settings_service.py`, `utils/email_utils.py`)
- [x] Authentication/Authorization (`auth/`, `api/v1/auth.py`)
- [x] Background job execution model (`BackgroundTasks`, `process_meeting_in_background`)
- [x] LangGraph checkpointing & serialization (`graph.py`, `utils/cancellation.py`)
- [x] PII redaction parsing & repair logic (`Nodes/vi_redaction.py`)
- [x] Local task file storage (`storage/task_storage.py`)
- [x] Frontend review components (`components/meetings/`)
- [x] Provider catalog & model validation (`config/providers.py`)