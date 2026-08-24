# Admin Dashboard & User Settings Design

**Date:** 2026-08-19
**Status:** Draft for review

---

## 1. Problem Statement

The meeting notes agent currently lacks:
- Admin visibility into system usage (users, meetings, tokens, credits)
- User-facing settings page for profile, password, usage, and credits
- Quota/credit enforcement on meeting processing
- Role-based access control in the frontend (admin vs user views)

---

## 2. Requirements Summary

### Admin Dashboard
- System overview: total users, active users, meetings processed, total tokens
- User management table with: email, name, role, monthly meetings, quota, credits, status
- Full CRUD on users: change role, adjust quota, add/remove credits, suspend/activate, delete

### User Settings
- Profile: view email, edit name, change password
- Usage: current month meetings processed vs quota, tokens used, reset date
- Credits: current balance, transaction history

### Quota & Credit System
- Credits charged per meeting processed (flat fee)
- Monthly meeting quota per user (default 20/month)
- Hard enforcement: block processing when quota exceeded (403)
- Calendar month reset (1st of month), no rollover
- Token tracking: total tokens per meeting across all LLM calls

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                  │
│  /admin          /settings           /meetings              │
│  AdminDashboard  SettingsPage        MeetingList            │
└──────────────────────────┬──────────────────────────────────┘
                           │ API calls (axios with cookies)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  /admin/*        /users/*           /meetings*              │
│  AdminRouter     UserRouter         MeetingRouter           │
│  require_admin   require_user       require_user            │
└──────────────────────────┬──────────────────────────────────┘
                           │ SQLAlchemy / raw SQL
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL                               │
│  users (existing)                                           │
│  + role column                                              │
│  meetings (existing)                                        │
│  + tokens_used column                                       │
│  user_quotas (NEW)                                          │
│  user_credits (NEW)                                         │
│  user_usage (NEW, optional for history)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

### 4.1 New Tables

#### `user_quotas`
| Column | Type | Constraints |
|--------|------|-------------|
| `user_id` | UUID | PK, FK → users.id |
| `monthly_meeting_limit` | INTEGER | DEFAULT 20 |
| `monthly_credits` | INTEGER | DEFAULT 500 (credits granted per month) |
| `created_at` | TIMESTAMPTZ | DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() |

#### `user_credits`
| Column | Type | Constraints |
|--------|------|-------------|
| `user_id` | UUID | PK, FK → users.id |
| `balance` | INTEGER | DEFAULT 0 |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() |

#### `user_usage` (monthly rollup for history)
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK, gen_random_uuid() |
| `user_id` | UUID | FK → users.id |
| `month` | DATE | First day of month (e.g., '2026-08-01') |
| `meetings_processed` | INTEGER | DEFAULT 0 |
| `tokens_used` | INTEGER | DEFAULT 0 |
| `credits_consumed` | INTEGER | DEFAULT 0 |
| `created_at` | TIMESTAMPTZ | DEFAULT now() |
| `updated_at` | TIMESTAMPTZ | DEFAULT now() |
| **Unique** | | `(user_id, month)` |

### 4.2 Modified Existing Tables

#### `meetings`
- Add `tokens_used` INTEGER DEFAULT 0

---

## 5. Token Tracking Implementation

### 5.1 State Schema Addition
In `src/meeting_notes_agent/state_schema.py`:
```python
class MeetingState(TypedDict):
    # ... existing fields ...
    tokens_used_accrued: int  # accumulates across LLM nodes
```

### 5.2 LLM Node Token Counting
Each LLM node (`ii_transcribe_audio`, `iii_clean_transcript`, `iv_summerize`, `v_extraction`, `vi_redaction`, `vii_PM_tasks`, `viii_emailing`) will:
1. After successful LLM call, extract token usage from response
2. Update state: `tokens_used_accrued += response.usage.total_tokens`

For OpenAI, this is `response.usage.total_tokens` from the completion response.

### 5.3 Persistence
In the final store node (`ix_store.py`) or when meeting completes:
```python
# Save total tokens to meetings.tokens_used
UPDATE meetings SET tokens_used = :total_tokens WHERE id = :meeting_id
```

---

## 6. Admin API Endpoints

### Base: `/admin` (requires `require_admin`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/dashboard` | System stats: total_users, active_users_24h, meetings_today, tokens_today, meetings_this_month, tokens_this_month |
| GET | `/admin/users` | Paginated user list with usage (params: page, limit, search, role_filter) |
| GET | `/admin/users/{user_id}` | User detail with usage history |
| PATCH | `/admin/users/{user_id}` | Update: role, monthly_meeting_limit, credits, is_active |
| DELETE | `/admin/users/{user_id}` | Soft delete (set is_active=false) or hard delete |

### Response Shapes

**Dashboard:**
```json
{
  "total_users": 150,
  "active_users_24h": 12,
  "meetings_today": 8,
  "tokens_today": 45000,
  "meetings_this_month": 234,
  "tokens_this_month": 1250000
}
```

**User List Item:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "monthly_meeting_limit": 20,
  "credits_balance": 450,
  "meetings_this_month": 5,
  "tokens_this_month": 25000,
  "quota_reset_date": "2026-09-01"
}
```

---

## 7. User API Endpoints

### Base: `/users` (requires `require_user`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/profile` | Current user's profile |
| PATCH | `/users/profile` | Update name (email immutable) |
| POST | `/users/change-password` | Change password (old + new) |
| GET | `/users/usage` | Current month usage + quota |
| GET | `/users/credits` | Credit balance + recent transactions |

### Response Shapes

**Usage:**
```json
{
  "month": "2026-08-01",
  "meetings_processed": 5,
  "monthly_quota": 20,
  "quota_remaining": 15,
  "tokens_used": 25000,
  "quota_reset_date": "2026-09-01"
}
```

**Credits:**
```json
{
  "balance": 450,
  "transactions": [
    {"date": "2026-08-15", "type": "meeting_processed", "amount": -1, "description": "Meeting: Q3 Planning"},
    {"date": "2026-08-10", "type": "admin_grant", "amount": 500, "description": "Monthly credit grant"}
  ]
}
```

---

## 8. Quota Enforcement

### Location
In `src/meeting_notes_agent/graph.py`, at the start of `create_meeting` node or as a pre-check in the input node.

### Logic
```python
def check_quota(user_id: str) -> bool:
    # Get current month start
    month_start = date.today().replace(day=1)
    
    # Get or create quota record
    quota = db.query(UserQuota).filter_by(user_id=user_id).first()
    if not quota:
        quota = UserQuota(user_id=user_id, monthly_meeting_limit=20)
        db.add(quota)
    
    # Count meetings this month
    meetings_this_month = db.query(Meeting).filter(
        Meeting.user_id == user_id,
        Meeting.created_at >= month_start
    ).count()
    
    if meetings_this_month >= quota.monthly_meeting_limit:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly meeting quota ({quota.monthly_meeting_limit}) exceeded. Resets on {month_start + timedelta(days=32):%Y-%m-%d}."
        )
    
    # Check credits
    credits = db.query(UserCredits).filter_by(user_id=user_id).first()
    if credits and credits.balance <= 0:
        raise HTTPException(
            status_code=403,
            detail="Insufficient credits. Please contact admin."
        )
    
    return True
```

### Credit Deduction
After successful meeting processing, decrement credits:
```python
credits.balance -= 1
db.commit()
```

---

## 9. Frontend Pages

### 9.1 `/admin` — Admin Dashboard
**Components:**
- `AdminDashboard.tsx` (new page)
- `UserTable.tsx` (new component)
- `UserEditModal.tsx` (new component)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Admin Dashboard                              [Logout]   │
├─────────────────────────────────────────────────────────┤
│ [Total Users: 150]  [Active Today: 12]  [Meetings: 234] │
│ [Tokens This Month: 1.25M]  [Credits Granted: 75K]      │
├─────────────────────────────────────────────────────────┤
│ Search: [_______]  Role: [All ▼]  Status: [All ▼]       │
├─────────────────────────────────────────────────────────┤
│ Email          | Name      | Role | Meetings | Quota | Credits │ Status | Actions │
│ user@ex.com    | John Doe  | user | 5 / 20   | 20    | 450     │ Active │ [Edit]  │
│ admin@ex.com   | Admin     | admin| 0 / -    | -     | -       │ Active │ [Edit]  │
└─────────────────────────────────────────────────────────┤
│                    [← Prev]  Page 1 of 3  [Next →]      │
└─────────────────────────────────────────────────────────┘
```

**Edit Modal Fields:**
- Role: [user ▼ | admin]
- Monthly Meeting Quota: [20]
- Credits Balance: [450]
- Status: [Active ▼ | Suspended]
- [Save] [Cancel]

### 9.2 `/settings` — User Settings
**Components:**
- `SettingsPage.tsx` (new page)
- `ProfileSection.tsx`, `UsageSection.tsx`, `CreditsSection.tsx` (new components)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Settings                                                │
├─────────────────────────────────────────────────────────┤
│ ┌─ Profile ─────────────────────────────────────────┐   │
│ │ Email: user@example.com (cannot change)           │   │
│ │ Full Name: [John Doe              ] [Save]        │   │
│ │                                                     │   │
│ │ Change Password                                   │   │
│ │ Current: [********]  New: [********]  Confirm: [**]│   │
│ │                                                    [Save]│
│ └───────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─ Usage This Month ────────────────────────────────┐   │
│ │ Meetings: ████████░░░░░░░░░░  5 / 20 (25%)        │   │
│ │ Tokens Used: 25,000                                │   │
│ │ Resets on: September 1, 2026                      │   │
│ └───────────────────────────────────────────────────┘   │
│                                                         │
│ ┌─ Credits ──────────────────────────────────────────┐   │
│ │ Balance: 450 credits                               │   │
│ │                                                     │   │
│ │ Recent Transactions:                               │   │
│ │ Aug 15  -1  Meeting: "Q3 Planning"                │   │
│ │ Aug 10 +500 Monthly grant                          │   │
│ └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 10. Frontend Routing Updates

### `App.tsx`
```tsx
<Routes>
  {/* ... existing routes ... */}
  <Route path="/admin" element={<RequireAuth><AdminDashboard /></RequireAuth>} />
  <Route path="/settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />
</Routes>
```

### `Navbar.tsx`
- Add "Settings" link for all users
- Add "Admin Panel" link for admin role (already exists)

---

## 11. Security & Permissions

| Endpoint | Required Role | Notes |
|----------|---------------|-------|
| `/admin/*` | `admin` | `require_admin` dependency |
| `/users/profile` | `user` or `admin` | Users see own profile; admins can view any |
| `/users/change-password` | `user` or `admin` | Own password only |
| `/users/usage` | `user` or `admin` | Own usage; admins see any |
| `/users/credits` | `user` or `admin` | Own credits; admins see any |

---

## 12. Migration Strategy

1. **Run SQL migration** to add tables and columns
2. **Backfill** `user_quotas` for existing users (default 20 meetings, 500 credits)
3. **Backfill** `user_credits` for existing users (default 500)
4. **Deploy** backend changes
5. **Deploy** frontend changes

---

## 13. Testing Checklist

- [ ] Admin can view dashboard with correct stats
- [ ] Admin can edit user role, quota, credits, status
- [ ] Admin can delete/suspend users
- [ ] User can view own profile and edit name
- [ ] User can change password
- [ ] User sees correct usage and quota
- [ ] User sees credit balance and transactions
- [ ] Quota enforcement blocks at limit (403)
- [ ] Credit deduction on meeting completion
- [ ] Token tracking accumulates correctly across LLM nodes
- [ ] Monthly reset works (test with time travel or manual date)

---

## 14. Open Questions (Resolved)

1. **Token tracking granularity** → Total per meeting (not per-node)
2. **Credit model** → Credits per meeting processed (flat)
3. **Admin actions** → Full CRUD + quota management
4. **User settings** → Full profile + usage + credits + password
5. **Quota enforcement** → Hard block with 403
6. **Quota reset** → Calendar month, no rollover

---

## 15. Next Steps

1. User reviews this spec
2. Invoke `writing-plans` skill to create implementation plan
3. Implement database migrations
4. Implement backend APIs
5. Implement frontend pages
6. Test end-to-end

---

*End of Design Document*