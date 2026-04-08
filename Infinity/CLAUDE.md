# Infinity — MFD Digital Diary API

## What this is
A **FastAPI backend** for financial advisors (Mutual Fund Distributors) to manage clients, leads, tasks, meetings, goals, portfolios, and financial calculators. No frontend in this repo — it's a pure REST API.

## Tech Stack
- **Framework:** FastAPI + Uvicorn
- **Database:** Supabase (PostgreSQL + PostgREST)
- **Auth:** Supabase Auth + JWT Bearer tokens
- **Validation:** Pydantic v2
- **AI:** OpenAI + Google Gemini (voice/intent parsing)
- **Other:** ReportLab (PDFs), APScheduler (background jobs), Firebase (push notifications), Google Sheets sync

## Project Structure
```
backend/app/
├── main.py              # App setup, middleware, router registration
├── config.py            # Environment variables (Settings class)
├── database.py          # Supabase client init (RLS + Admin)
├── auth/dependencies.py # JWT validation, get_current_user()
├── constants/           # enums.py, calculator_constants.py
├── middleware/           # CORS, rate limiting, logging, security headers
├── models/              # Pydantic request/response schemas (23 files)
├── routers/             # API endpoints (25 files, 125+ endpoints)
├── services/            # Business logic (27 files)
├── jobs/                # APScheduler background tasks
├── utils/               # Financial formulas, PDF generator
└── prompts/             # AI prompt templates
```

## Key Patterns

### Database Access
- `get_supabase_client()` / `supabase` → **user-scoped**, RLS enforced. Use for user data.
- `supabase_admin` → **service role**, bypasses RLS. Use for system-level data (webhooks, caches, cross-user operations).
- Services are instantiated with `user_id` for RLS scoping.

### Request Flow
`Router (auth + validation) → Service (business logic) → Supabase (database)`

### Serialization
- Always use `model_dump(mode="json", exclude_unset=True)` when sending Pydantic data to Supabase.
- `mode="json"` converts dates, UUIDs, and enums to JSON-safe strings automatically.
- **Do NOT** add manual `.isoformat()`, `str(uuid)`, or `hasattr(value, "value")` workarounds.

### Enums (backend/app/constants/enums.py)
- Enum `.value` strings must match the PostgreSQL enum values exactly.
- Python member names use `v_` prefix when they start with a digit (e.g., `v18_to_24 = "18_to_24"`).
- Class names use PascalCase: `AumBracketType`, `SipBracketType` (not `AUMBracketType`).

### Auth
- All endpoints require JWT Bearer token via `get_current_user` dependency.
- Exception: `/health` and `/webhooks/*` (webhooks use `X-API-Key` header).

### API Prefix
All endpoints under `/api/v1/` except health check (`/health`).

## Core Entities
| Entity | Table | What it is |
|--------|-------|------------|
| Lead | leads | Sales prospect before conversion |
| Client | clients | Converted lead, full financial profile |
| Task | tasks | Daily tasks with carry-forward |
| Touchpoint | touchpoints | Meetings with MoM (minutes of meeting) |
| Business Opportunity | business_opportunities | Sales pipeline tracking |
| Goal | goals | Financial goals with sub-goals |
| Client Product | client_products | Investment holdings & transactions |
| Campaign | campaigns | Bulk messaging (WhatsApp/Email) |

## Known Issues Being Fixed
- Enum values in `enums.py` have wrong prefixes (e.g., `"l1_to_2_5"` should be `"1_to_2_5"`)
- `model_dump()` calls missing `mode="json"` across all services
- Some Pydantic models don't match DB schema (phantom fields, wrong types, missing columns)
- See changelog PDF for full details

## Docs
Existing documentation in `/docs/`:
- `API_ENDPOINTS.md` — All endpoints
- `DATABASE_SCHEMA.md` — PostgreSQL schema
- `PROJECT_STRUCTURE.md` — Architecture overview
- `PYDANTIC_MODELS.md` — All Pydantic schemas
- `tables.md` — Table definitions
