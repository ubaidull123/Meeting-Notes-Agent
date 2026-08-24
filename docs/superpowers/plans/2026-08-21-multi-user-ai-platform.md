# Multi-User Configurable AI Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the meeting-notes app from application-wide environment credentials to a multi-user configurable AI platform where every authenticated user can independently configure LLM provider/model/API key, transcription provider/model/API key, email provider/settings, and choose between BYOK or application credits. Full-stack: every backend feature exposed via API and implemented in frontend, with actual meeting processing using the selected configuration.

**Architecture:** Multi-tier resolution (meeting override → user default → application default). Encrypted credential storage (AES-GCM with HKDF-derived key). Provider factory/registry pattern for LLM and transcription (OpenAI fully implemented, stubs ready for Groq/Anthropic/Gemini/OpenRouter). Usage-based credit ledger with configurable pricing per provider/model. Transactional credit deduction before processing. State passes resolved configs to LangGraph nodes.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL/SQLite, LangGraph, React, TanStack Query, Tailwind, Pydantic, pytest, Cryptography (AES-GCM), OpenAI SDK, LangChain

**Spec:** User requirements from conversation (37 requirements covering database → backend services → API → frontend API client → frontend settings UI → actual meeting processing)

## Global Constraints

- **Full-stack rule:** Every backend feature MUST have API endpoint + frontend UI + affect actual processing
- **Secrets never exposed:** API keys encrypted at rest (AES-GCM with CREDENTIAL_ENCRYPTION_KEY env), masked in responses (••••abcd)
- **No silent fallbacks:** BYOK without valid key → error, not app credits
- **Credits:** Usage-based (tokens + audio duration), configurable pricing per provider/model
- **Meeting overrides:** Resolution order: meeting override → user default → application default
- **Email:** Resend, Mailgun, SMTP as user-configurable options; app-owned email as separate mode
- **Tests:** Backend unit + integration, frontend lint + build must pass
- **Encryption:** Isolate behind service for future KMS replacement

---

## Data & API Contract

All subagents must follow this contract exactly:

### Database Models (src/meeting_notes_agent/database/models_ai_config.py)

```python
class ProviderType(str, PyEnum):
    OPENAI = "openai"
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    RESEND = "resend"
    MAILGUN = "mailgun"
    SMTP = "smtp"

class AIUsageMode(str, PyEnum):
    APP_CREDITS = "app_credits"
    BYOK = "byok"

class UserAIConfig(Base):
    __tablename__ = "user_ai_config"
    user_id: int  # FK users.id, PK
    llm_usage_mode: AIUsageMode
    llm_provider: ProviderType
    llm_model: str | None
    llm_credential_id: int | None  # FK user_credentials.id
    transcription_usage_mode: AIUsageMode
    transcription_provider: ProviderType
    transcription_model: str | None
    transcription_credential_id: int | None
    updated_at: datetime

class UserCredential(Base):
    __tablename__ = "user_credentials"
    id: int (PK, autoincrement)
    user_id: int (FK)
    provider: ProviderType
    api_key_encrypted: str | None
    api_key_hint: str | None (masked, last 4 chars)
    config_encrypted: str | None (for SMTP config)
    is_valid: bool
    last_tested_at: datetime | None
    last_test_error: str | None
    created_at: datetime
    updated_at: datetime
    UniqueConstraint(user_id, provider)

class UserEmailConfig(Base):
    __tablename__ = "user_email_config"
    user_id: int (FK, PK)
    email_mode: AIUsageMode
    provider: ProviderType
    sender_name: str | None
    sender_email: str | None
    reply_to_email: str | None
    credential_id: int | None
    smtp_host: str | None
    smtp_port: int | None
    smtp_username: str | None
    smtp_use_tls: bool (default True)
    updated_at: datetime

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"
    id: UUID (PK)
    user_id: int (FK)
    meeting_id: UUID | None (FK)
    amount: int (negative = debit)
    balance_after: int
    transaction_type: str ("meeting_processing", "admin_adjustment", "refund")
    service_type: str | None ("llm", "transcription", "email")
    provider: str | None
    model: str | None
    usage_mode: AIUsageMode | None
    usage_metadata: JSON | None
    description: str | None
    created_at: datetime

class UsageRecord(Base):
    __tablename__ = "usage_records"
    id: UUID (PK)
    user_id: int (FK)
    meeting_id: UUID (FK)
    service_type: str ("llm", "transcription", "email")
    provider: str
    model: str
    usage_mode: AIUsageMode
    input_tokens: int
    output_tokens: int
    audio_duration_seconds: int
    credits_cost: int
    status: str ("completed", "failed")
    error_message: str | None
    created_at: datetime

class MeetingAIOverride(Base):
    __tablename__ = "meeting_ai_overrides"
    meeting_id: UUID (PK, FK)
    llm_usage_mode: AIUsageMode | None
    llm_provider: ProviderType | None
    llm_model: str | None
    transcription_usage_mode: AIUsageMode | None
    transcription_provider: ProviderType | None
    transcription_model: str | None
    email_mode: AIUsageMode | None
    email_provider: ProviderType | None
    created_at: datetime
    updated_at: datetime

class PricingRule(Base):
    __tablename__ = "pricing_rules"
    id: int (PK)
    provider: str
    model: str
    service_type: str ("llm", "transcription")
    input_token_price: int (credits per 1K tokens)
    output_token_price: int
    audio_minute_price: int
    flat_fee: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    UniqueConstraint(provider, model, service_type)
```

### Provider Catalog (src/meeting_notes_agent/config/providers.py)
```python
PROVIDER_CATALOG = {
    "openai": {"name": "OpenAI", "capabilities": ["chat", "transcription"], "models": {"chat": [...], "transcription": [...]}},
    "groq": {"name": "Groq", "capabilities": ["chat"], "models": {"chat": [...]}},
    "anthropic": {"name": "Anthropic", "capabilities": ["chat"], "models": {"chat": [...]}},
    "gemini": {"name": "Google Gemini", "capabilities": ["chat"], "models": {"chat": [...]}},
    "openrouter": {"name": "OpenRouter", "capabilities": ["chat"], "models": {"chat": [...]}},
    "resend": {"name": "Resend", "capabilities": ["email"], "models": {}},
    "mailgun": {"name": "Mailgun", "capabilities": ["email"], "models": {}},
    "smtp": {"name": "SMTP", "capabilities": ["email"], "models": {}},
}
# Functions: get_available_providers(capability), get_available_models(provider, capability)
```

### Pricing Config (src/meeting_notes_agent/config/pricing.py)
```python
def calculate_credits(provider, model, service_type, input_tokens=0, output_tokens=0, audio_duration_seconds=0) -> int:
    # Look up PricingRule, calculate: ceil(input/1000 * input_price) + ceil(output/1000 * output_price) + (audio_seconds/60 * audio_price) + flat_fee
    # Minimum 1 credit if any usage
```

### Provider Factory (src/meeting_notes_agent/llms/providers/__init__.py)
```python
class LLMProviderFactory:
    @staticmethod
    def get_provider(provider: ProviderType, api_key: str, model: str, **kwargs) -> LLMProvider
    @staticmethod
    def get_available_providers() -> list[str]
    @staticmethod
    def is_available(provider: ProviderType) -> bool

class TranscriptionProviderFactory:
    @staticmethod
    def get_provider(provider: ProviderType, api_key: str, model: str, **kwargs) -> TranscriptionProvider
    @staticmethod
    def get_available_providers() -> list[str]
    @staticmethod
    def is_available(provider: ProviderType) -> bool
```

### Credential Encryption (src/meeting_notes_agent/services/credential_encryption.py)
```python
class CredentialEncryptionService:
    def __init__(self, master_key: str | None = None)  # From settings.credential_encryption_key
    def encrypt(self, plaintext: str) -> str  # Returns base64(nonce + ciphertext)
    def decrypt(self, encrypted: str) -> str
    @staticmethod
    def mask_key(api_key: str) -> str  # Returns ••••abcd format
```

### Settings Service (src/meeting_notes_agent/services/ai_settings_service.py)
```python
class AISettingsService:
    def __init__(self, db: Session)
    
    # Config CRUD
    def get_ai_config(self, user_id: int) -> UserAIConfig
    def update_llm_settings(self, user_id, usage_mode, provider, model, credential_id) -> UserAIConfig
    def update_transcription_settings(self, user_id, usage_mode, provider, model, credential_id) -> UserAIConfig
    
    # Credential CRUD
    def save_credential(self, user_id, provider, api_key, config=None) -> UserCredential
    def get_credential(self, user_id, provider) -> Optional[UserCredential]
    def list_credentials(self, user_id) -> list[UserCredential]
    def delete_credential(self, user_id, provider) -> bool
    def get_decrypted_credential(self, user_id, provider) -> Optional[str]
    def test_credential(self, user_id, provider) -> dict  # {valid, provider, message}
    
    # Resolution (meeting override → user default → app default)
    def resolve_llm_config(self, user_id, meeting_override: dict | None) -> dict
    def resolve_transcription_config(self, user_id, meeting_override: dict | None) -> dict
```

### Email Settings Service (src/meeting_notes_agent/services/email_settings_service.py)
```python
class EmailSettingsService:
    def __init__(self, db: Session)
    def get_email_config(self, user_id: int) -> UserEmailConfig
    def update_email_config(self, user_id, **kwargs) -> UserEmailConfig
    def get_resolved_email_config(self, user_id, meeting_override: dict | None) -> dict
    def test_email_connection(self, user_id: int) -> dict
```

### Credits Service (src/meeting_notes_agent/services/credits_service.py)
```python
class CreditsService:
    def __init__(self, db: Session)
    def get_balance(self, user_id: int) -> int
    def check_sufficient_credits(self, user_id: int, required: int) -> bool
    def deduct_credits(self, user_id, amount, meeting_id=None, **kwargs) -> CreditTransaction
    def add_credits(self, user_id, amount, reason, admin_user_id=None) -> CreditTransaction
    def record_usage(self, user_id, meeting_id, service_type, provider, model, usage_mode, ...) -> UsageRecord
    def record_usage_failed(self, user_id, meeting_id, ...) -> UsageRecord
    def get_usage_history(self, user_id, limit=50) -> list[UsageRecord]
    def get_transactions(self, user_id, limit=50) -> list[CreditTransaction]
```

### Meeting Override Service (src/meeting_notes_agent/services/meeting_override_service.py)
```python
class MeetingOverrideService:
    def __init__(self, db: Session)
    def get_override(self, meeting_id: UUID) -> Optional[MeetingAIOverride]
    def set_override(self, meeting_id, **kwargs) -> MeetingAIOverride
    def clear_override(self, meeting_id: UUID) -> bool
    def to_dict(self, meeting_id: UUID) -> Optional[dict]
```

### API Endpoints (src/meeting_notes_agent/api/v1/settings.py)
```
GET  /api/v1/settings/providers                              # Provider catalog
GET  /api/v1/settings/ai                                     # User AI config
PUT  /api/v1/settings/ai                                     # Update AI config
GET  /api/v1/settings/credentials                            # List credentials
POST /api/v1/settings/credentials                           # Add credential
DELETE /api/v1/settings/credentials/{provider}             # Delete credential
POST /api/v1/settings/credentials/test?provider=...         # Test credential
GET  /api/v1/settings/email                                  # Email config
PUT  /api/v1/settings/email                                  # Update email config
GET  /api/v1/settings/credits                                # Balance
GET  /api/v1/settings/credits/transactions                   # Transaction history
GET  /api/v1/settings/usage                                  # Usage history
GET  /api/v1/settings/meetings/{id}/override               # Meeting override
PUT  /api/v1/settings/meetings/{id}/override                 # Set override
DELETE /api/v1/settings/meetings/{id}/override              # Clear override
```

### Frontend API Client (frontend/src/api/settings.ts)
All typed hooks matching the above endpoints, using the existing `apiClient` (axios with JWT auth).

### Frontend Types (frontend/src/types/settings.ts)
TypeScript types mirroring all Python schemas above.

---

## Task Decomposition

### Task 1: Database Schema - User AI Configuration Tables
- Create: `src/meeting_notes_agent/database/models_ai_config.py` (all 7 models + enums)
- Modify: `src/meeting_notes_agent/database/models.py` (back_populates relationships)
- Modify: `src/meeting_notes_agent/database/__init__.py` (export new models)
- Test: `tests/test_ai_config_models.py`

### Task 2: Credential Encryption Service
- Create: `src/meeting_notes_agent/services/credential_encryption.py`
- Create: `tests/test_credential_encryption.py`
- Modify: `src/meeting_notes_agent/core/config.py` (add credential_encryption_key setting)
- Add `cryptography` to pyproject.toml dependencies

### Task 3: Provider Catalog & Pricing Configuration
- Create: `src/meeting_notes_agent/config/providers.py`
- Create: `src/meeting_notes_agent/config/pricing.py`
- Create: `tests/test_provider_catalog.py`
- Create: `tests/test_pricing.py`

### Task 4: LLM Provider Factory (OpenAI fully implemented, stubs for others)
- Create: `src/meeting_notes_agent/llms/base.py` (abstract interfaces)
- Create: `src/meeting_notes_agent/llms/providers/openai_provider.py`
- Create: `src/meeting_notes_agent/llms/providers/__init__.py` (factory + registry)
- Create: `src/meeting_notes_agent/llms/transcription/base.py`
- Create: `src/meeting_notes_agent/llms/transcription/openai_transcription.py`
- Create: `src/meeting_notes_agent/llms/transcription/__init__.py`
- Test: `tests/test_llm_provider_factory.py`, `tests/test_transcription_factory.py`

### Task 5: AI Settings Service
- Create: `src/meeting_notes_agent/services/ai_settings_service.py`
- Create: `tests/test_ai_settings_service.py`
- Modify: `src/meeting_notes_agent/database/repositories.py` (add repos for new models)

### Task 6: Email Settings Service
- Create: `src/meeting_notes_agent/services/email_settings_service.py`
- Create: `tests/test_email_settings_service.py`

### Task 7: Credits Service (Transactional Ledger)
- Create: `src/meeting_notes_agent/services/credits_service.py`
- Create: `tests/test_credits_service.py`

### Task 8: Meeting Override Service
- Create: `src/meeting_notes_agent/services/meeting_override_service.py`
- Create: `tests/test_meeting_override_service.py`

### Task 9: Backend API Endpoints - Settings
- Create: `src/meeting_notes_agent/api/v1/settings.py`
- Create: `src/meeting_notes_agent/schemas/settings.py`
- Create: `tests/test_settings_api.py`
- Modify: `src/meeting_notes_agent/api/v1/__init__.py` (register router)

### Task 10: Integrate Provider Resolution into Processing Pipeline
- Modify: `src/meeting_notes_agent/state_schema.py` (add config fields to state)
- Modify: `src/meeting_notes_agent/services/processing_service.py` (resolve configs before processing)
- Modify: `src/meeting_notes_agent/graph.py` (pass configs through)
- Modify: `src/meeting_notes_agent/Nodes/ii_transcribe_audio.py` (use provider factory)
- Modify: `src/meeting_notes_agent/Nodes/iv_summarize.py` (use provider factory)
- Create: `tests/test_processing_integration.py`

### Task 11: Frontend Types & API Client
- Create: `frontend/src/types/settings.ts`
- Create: `frontend/src/api/settings.ts`

### Task 12: Frontend Settings UI - 4-Tab Page
- Modify: `frontend/src/extraPages.tsx` (SettingsPage → 4 tabs)
- Create: `frontend/src/components/settings/AISettingsTab.tsx`
- Create: `frontend/src/components/settings/TranscriptionSettingsTab.tsx` (part of AI tab)
- Create: `frontend/src/components/settings/EmailSettingsTab.tsx`
- Create: `frontend/src/components/settings/CreditsTab.tsx`

### Task 13: Meeting Override UI
- Modify: `frontend/src/pages.tsx` (CreateMeetingPage - add override button)
- Modify: `frontend/src/extraPages.tsx` (MeetingPage - add override button)
- Create: `frontend/src/components/settings/MeetingOverrideModal.tsx`

### Task 14: Backend Integration Tests
- Create: `tests/test_ai_settings_integration.py`
- Create: `tests/test_credits_integration.py`
- Create: `tests/test_meeting_override_integration.py`

### Task 15: Full Test Suite & Verification
- Run all backend tests (`pytest tests/ -v`)
- Run frontend lint (`npm run lint`)
- Run frontend build (`npm run build`)

### Task 16: Feature Matrix Verification & Documentation
- Create: `FEATURE_MATRIX.md`
- Full E2E verification checklist

---

## Execution Order (dependency graph)

```
Task 1 (DB models) → Task 2 (encryption) → Task 4 (providers)
                 → Task 3 (catalog/pricing) → Task 4 (providers)
Task 2, 3, 4 → Task 5 (AI settings service)
Task 2 → Task 6 (email settings)  
Task 1 → Task 7 (credits service)
Task 1 → Task 8 (meeting override service)
Task 5, 6, 7, 8 → Task 9 (API endpoints)
Task 9 → Task 11 (frontend types/api)
Task 11 → Task 12 (frontend UI)
Task 10 (pipeline integration) depends on Task 1, 2, 3, 4, 5, 7, 8
Task 9, 12 → Task 13 (override UI)
All → Task 14 (integration tests)
All → Task 15 (full verification)
All → Task 16 (feature matrix)
```

Tasks 1-8 can run with subagents in parallel where independent. Tasks 9+ should be sequential. Task 10 requires careful integration — must be reviewed thoroughly.
