# E2E Testing Changelog — Bugs Found & Fixed

**Date:** 2026-03-19
**Scope:** E2E test suite creation + all runtime bugs caught by those tests
**Result:** 41 tests written, 9 bugs found and fixed across 5 service files + 1 model file

---

## 1. Test Infrastructure Created

| File | Purpose |
|------|---------|
| `backend/tests/__init__.py` | Package marker |
| `backend/tests/conftest.py` | Shared fixtures — httpx `AsyncClient` wired to the FastAPI app via `ASGITransport`, auth dependency overridden to inject a fixed test user (no live JWT needed), `.env` auto-loaded |
| `backend/tests/test_e2e.py` | 41 E2E tests across 12 test classes |
| `backend/pytest.ini` | Pytest config with `asyncio_mode = auto` |

### Test Coverage

| Test Class | Endpoints Tested | What It Catches |
|------------|-----------------|-----------------|
| `TestHealth` | `GET /` | App starts |
| `TestLeads` | List, Create, Get, Update, Delete, Status Update, Today Follow-ups | `is_deleted` column, NULL phone, `sourced_by` mapping |
| `TestClients` | List, Create, Get, Update, Delete, Overview, Cash Flow, Duplicate Check | `total_aum`/`sip` mapping, `sourced_by` mapping |
| `TestTasks` | List, Create, Get, Update, Delete, Complete, Carry Forward, Today, Bulk Complete | `description`/`title` mapping, `original_date` alias |
| `TestTouchpoints` | List, Create, Get, Update, Delete, Complete, Reschedule, Upcoming, MOM Update | `purpose`/`agenda` mapping |
| `TestBusinessOpportunities` | List, Create, Get, Update, Delete, Pipeline, Outcome, Stage | `additional_info`/`notes` mapping |
| `TestGoals` | List, Create, Get, Update, Delete, With Subgoals, Progress, Client Goals | Goal CRUD full cycle |
| `TestDashboard` | Stats, Today, Pipeline, Conversions, Growth | Column name mismatches in aggregate queries |
| `TestSearch` | Global, Clients, Leads, Tasks, Recent | Column names in select + filter clauses |
| `TestProfile` | Get Profile | Profile auto-creation |
| `TestCalculators` | SIP Calculator (smoke) | No 500 errors |
| `TestDataIO` | Template download, Export clients (smoke) | No 500 errors |
| `TestConvertLead` | Full lead-to-client conversion flow | NOT NULL `gender`, FK constraints |
| `TestEdgeCases` | All optional fields, lead-linked touchpoints, 404s on fake IDs | Enum serialization, field completeness |

---

## 2. Bugs Found & Fixed

### Bug 1: `dashboard_service.py` — `clients.aum` column does not exist

**Error:** `{'message': 'column clients.aum does not exist', 'code': '42703'}`
**Root cause:** Dashboard service selected `aum` and `sip_amount` from the `clients` table, but the actual DB columns are `total_aum` and `sip`.
**Affected endpoints:** `GET /api/v1/dashboard/stats`, `GET /api/v1/dashboard/growth`

**Fix in `services/dashboard_service.py`:**

| Location | Before | After |
|----------|--------|-------|
| `get_dashboard_stats()` select | `"id, aum, sip_amount"` | `"id, total_aum, sip"` |
| `get_dashboard_stats()` dict access | `client.get("aum")`, `client.get("sip_amount")` | `client.get("total_aum")`, `client.get("sip")` |
| `get_client_growth()` select | `"created_at, aum"` | `"created_at, total_aum"` |
| `get_client_growth()` dict access | `client.get("aum")` | `client.get("total_aum")` |

---

### Bug 2: `dashboard_service.py` — `clients.lead_tat_days` column does not exist

**Error:** `{'message': 'column clients.lead_tat_days does not exist', 'code': '42703'}`
**Root cause:** The `get_conversion_stats()` method selected `lead_tat_days` but the actual DB column is `tat_days`.
**Affected endpoint:** `GET /api/v1/dashboard/conversions`

**Fix in `services/dashboard_service.py`:**

| Location | Before | After |
|----------|--------|-------|
| `get_conversion_stats()` select | `"id, lead_tat_days"` | `"id, tat_days"` |
| `get_conversion_stats()` dict access | `client.get("lead_tat_days")` (x2) | `client.get("tat_days")` (x2) |

---

### Bug 3: `search_service.py` — `clients.aum` and `clients.sip_amount` do not exist

**Error:** `{'message': 'column clients.aum does not exist', 'code': '42703'}`
**Root cause:** Client search selected `aum, sip_amount` instead of the actual DB column names.
**Affected endpoints:** `GET /api/v1/search/`, `GET /api/v1/search/clients`

**Fix in `services/search_service.py`:**

```
Before: .select("id, name, phone, email, area, aum, sip_amount")
After:  .select("id, name, phone, email, area, total_aum, sip")
```

---

### Bug 4: `search_service.py` — `tasks.title` column does not exist

**Error:** `{'message': 'column tasks.title does not exist', 'code': '42703'}`
**Root cause:** Task search selected `title` and filtered with `title.ilike`, but the actual DB column is `description`.
**Affected endpoints:** `GET /api/v1/search/`, `GET /api/v1/search/tasks`

**Fix in `services/search_service.py`:**

```
Before: .select("id, title, description, due_date, status, priority")
         .or_(f"title.ilike.{search_pattern}," f"description.ilike.{search_pattern}")

After:  .select("id, description, due_date, status, priority")
         .ilike("description", search_pattern)
```

---

### Bug 5: `search_service.py` — `touchpoints.notes` column does not exist

**Error:** `{'message': 'column touchpoints.notes does not exist', 'code': '42703'}`
**Root cause:** Touchpoint search included `notes.ilike` in the `or_()` filter, but touchpoints table has no `notes` column (it was removed as a phantom field in the earlier model cleanup).
**Affected endpoint:** `GET /api/v1/search/` (global search)

**Fix in `services/search_service.py`:**

```
Before: .or_(f"purpose.ilike.{search_pattern},"
             f"notes.ilike.{search_pattern},"
             f"mom_text.ilike.{search_pattern}")

After:  .or_(f"purpose.ilike.{search_pattern},"
             f"mom_text.ilike.{search_pattern}")
```

---

### Bug 6: `client_service.py` — NOT NULL violation on `gender` during lead conversion

**Error:** `null value in column "gender" of relation "clients" violates not-null constraint (23502)`
**Root cause:** `convert_from_lead()` copies `gender` from the lead, but leads often don't have `gender` set. Since `clients.gender` is NOT NULL, the insert fails.
**Affected endpoint:** `POST /api/v1/clients/convert-from-lead`

**Fix in `services/client_service.py`:**

```
Before: "gender": lead.get("gender"),
After:  "gender": lead.get("gender") or "other",
```

---

### Bug 7: `lead.py` — Pydantic `date_from_datetime_inexact` on `conversion_date`

**Error:** `5 validation errors for LeadListResponse ... date_from_datetime_inexact`
**Root cause:** The `conversion_date` column is `timestamptz` in the DB (returns full datetime like `2026-03-19T13:36:13+00`), but `LeadResponse` declared it as `Optional[date]`. Pydantic v2.12 rejects lossy datetime-to-date coercion by default.
**Affected endpoint:** `GET /api/v1/leads/` (any list that includes converted leads)

**Fix in `models/lead.py`:**

Added a `BeforeValidator` that safely truncates datetime to date:

```python
def _coerce_date(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str) and "T" in v:
        return v.split("T")[0]
    return v

CoercedDate = Annotated[date, BeforeValidator(_coerce_date)]
```

Applied to `scheduled_date` and `conversion_date` in `LeadResponse`.

---

### Bug 8: `export_service.py` — Export silently drops `aum`/`sip_amount` columns

**Error:** No runtime error — silent data loss.
**Root cause:** Export service uses `select("*")` (returns DB column names `total_aum`, `sip`), then filters columns by a hardcoded list containing `aum`, `sip_amount`. Since those don't exist in the DataFrame, they're silently dropped.
**Affected endpoint:** `GET /api/v1/data/export/clients`

**Fix in `services/export_service.py`:**

```
Before: "aum", "sip_amount",
After:  "total_aum", "sip",
```

---

## 3. Summary of Files Modified

| File | Changes |
|------|---------|
| `services/dashboard_service.py` | 6 column name fixes (`aum` → `total_aum`, `sip_amount` → `sip`, `lead_tat_days` → `tat_days`) |
| `services/search_service.py` | 3 fixes: client columns, task column + filter, touchpoint phantom `notes` removed |
| `services/client_service.py` | 1 fix: `gender` default in `convert_from_lead` |
| `services/export_service.py` | 1 fix: export column names for clients |
| `models/lead.py` | 1 fix: `CoercedDate` type for `scheduled_date` and `conversion_date` |

---

## 4. How to Run Tests

```bash
cd Infinity/backend

# Install test dependencies (one time)
./venv/Scripts/pip install pytest "pytest-asyncio>=0.24"

# Run all E2E tests
./venv/Scripts/python -m pytest tests/test_e2e.py -v

# Run a specific test class
./venv/Scripts/python -m pytest tests/test_e2e.py::TestDashboard -v

# Run with short tracebacks and stop on first failure
./venv/Scripts/python -m pytest tests/test_e2e.py -v --tb=short -x
```

**Environment requirements:**
- `.env` file with valid `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`
- Tests use `TEST_USER_ID` env var (defaults to `567950d9-7a44-476d-b344-c5e48b722bd1`)
- Auth is overridden — no live JWT token needed
- Tests create and clean up their own data (creates temporary leads/clients/tasks, deletes them after)
