# Phase 1 Feature Matrix

| Feature | DB | API | Frontend | Runtime | Tests |
| --- | --- | --- | --- | --- | --- |
| Profile and locale | Yes | Yes | Yes | Stored for presentation defaults | Yes |
| AI provider, model, and mode | Yes | Yes | Yes | LLM resolution | Yes |
| Model tiers and advanced AI | Yes | Yes | Yes | Prompt/model invocation | Yes |
| Encrypted provider credentials | Yes | Yes | Yes | LLM, transcription, email | Yes |
| Transcription defaults | Yes | Yes | Yes | Transcription invocation | Yes |
| Meeting and output defaults | Yes | Yes | Yes | Processing graph and prompts | Yes |
| Custom meeting instructions | Yes | Yes | Yes | Summarization prompt context | Yes |
| Email settings and behavior | Yes | Yes | Yes | Delivery and approval graph | Yes |
| Credits and usage | Existing | Yes | Yes | Existing ledger | Yes |
| Notification preferences | Yes | Yes | Yes | Delivery deferred | Yes |
| Privacy preferences | Yes | Yes | Yes | Cleanup worker deferred | Yes |
| Security | Existing | Existing | Yes | Password and logout | Existing |

## Deferred

- Phase 2: projects, tags, advanced search, meeting-level controls, richer editable results, and advanced tasks.
- Phase 3: external notification delivery, retention cleanup worker, notification center, onboarding, exports, and email templates.
- Production/SaaS: account deletion workflow, server-side session management, billing, teams, organizations, and integrations.
