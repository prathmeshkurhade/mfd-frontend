# Backend Changelog — infinity-copy vs Infinity-Main

Changes made in the `infinity-copy` backend that need to be ported back to `Infinity-Main`.

---

## NEW: WhatsApp Forms API (3 new files)

Entire new feature — lets a WhatsApp bot create leads, tasks, touchpoints, and business opportunities on behalf of MFDs via webhook endpoints.

### `app/models/whatsapp_forms.py` (NEW)
- Pydantic models for all WhatsApp form payloads
- `WhatsAppFormBase` — base model requiring `mfd_phone` (10-digit number)
- `WALeadCreate`, `WATaskCreate`, `WATouchpointCreate`, `WABOCreate` — form-specific models with all fields optional except `mfd_phone`
- `WASearchRequest` / `WASearchResponse` — for client/lead lookup from WhatsApp
- `WAFormResponse` — standard success/error response

### `app/routers/whatsapp_forms.py` (NEW)
- 5 endpoints under `/api/v1/whatsapp-forms/`:
  - `POST /create-lead`
  - `POST /create-task`
  - `POST /create-touchpoint`
  - `POST /create-business-opportunity`
  - `POST /search` — search clients/leads by name
- Auth via `X-API-Key` header (same as other webhooks, no JWT)

### `app/services/whatsapp_form_service.py` (NEW)
- `WhatsAppFormService` class
- Resolves MFD phone number → `user_id` via `mfd_profiles` table (normalizes to `+91` format)
- Delegates to existing services (`LeadService`, `TaskService`, `TouchpointService`, `BOService`)
- Sets sensible defaults (e.g., lead status = `follow_up`, task priority = `medium`)

---

## MODIFIED: `app/main.py`

- **Added:** WhatsApp forms router registration
  ```python
  from app.routers import whatsapp_forms
  app.include_router(whatsapp_forms.router, prefix="/api/v1", tags=["WhatsApp Forms"])
  ```

---

## MODIFIED: `app/routers/dashboard.py`

- **Updated:** `get_today_summary` endpoint now accepts optional `target_date` query param (defaults to today)
  - Old: `GET /today-summary` — always uses today's date
  - New: `GET /today-summary?target_date=2026-03-20` — can fetch summary for any date
- **Added:** New `GET /calendar-events` endpoint
  - Takes `date_from` and `date_to` query params
  - Returns all tasks, touchpoints, lead follow-ups, and business opportunities in that date range
  - Each event has: `id`, `title`, `date`, `time`, `type`, `status`, `client_name`, `lead_name`

---

## MODIFIED: `app/services/dashboard_service.py`

- **Updated:** `get_today_summary()` now accepts optional `target_date` parameter
- **Added:** `get_calendar_events(date_from, date_to)` method (~145 lines)
  - Queries 4 tables: `tasks`, `touchpoints`, `leads`, `business_opportunities`
  - Batch-resolves client/lead names (avoids N+1 queries)
  - Only selects real DB columns (avoids phantom field errors)
  - Returns unified event list for calendar UI

---

## MODIFIED: `app/services/profile_service.py`

- **Added:** Dynamic column validation before updating `mfd_profiles`
  - Fetches existing row to get valid column names
  - Strips out any fields that don't exist in the DB
  - Prevents errors from sending non-existent columns to Supabase

---

## MODIFIED: `supabase/functions/import-from-sheet/index.ts`

- **Added:** `normalizePhone()` helper function — normalizes phone numbers to `+91XXXXXXXXXX` format
  - Strips non-digits, removes leading zeros
  - Handles `91XXXXXXXXXX` (12-digit) → `+91XXXXXXXXXX`
  - Handles `XXXXXXXXXX` (10-digit) → `+91XXXXXXXXXX`
- **Updated:** Lead and client dedup now uses normalized phone for matching
- **Updated:** Phone values from sheet are now normalized before insert

---

## MODIFIED: `supabase/functions/sheets-webhook/index.ts`

- **Added:** Same `normalizePhone()` helper function as above
- **Updated:** Lead and client phone numbers are normalized during sheet sync

---

## Summary Table

| File | Change Type | What |
|------|-------------|------|
| `app/models/whatsapp_forms.py` | NEW | WhatsApp form Pydantic models |
| `app/routers/whatsapp_forms.py` | NEW | WhatsApp form API endpoints |
| `app/services/whatsapp_form_service.py` | NEW | WhatsApp form business logic |
| `app/main.py` | MODIFIED | Register WhatsApp forms router |
| `app/routers/dashboard.py` | MODIFIED | Add `target_date` param + calendar-events endpoint |
| `app/services/dashboard_service.py` | MODIFIED | Add `target_date` support + calendar events method |
| `app/services/profile_service.py` | MODIFIED | Dynamic column validation for profile updates |
| `supabase/functions/import-from-sheet/index.ts` | MODIFIED | Phone normalization for sheet imports |
| `supabase/functions/sheets-webhook/index.ts` | MODIFIED | Phone normalization for sheet webhooks |
