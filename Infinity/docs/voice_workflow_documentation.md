# Voice workflow — Distributor 360

## What is this

A voice-to-action pipeline for the MFD Digital Diary app. Mutual Fund Distributors speak into the app — in Hindi, English, Marathi, or a mix — and the system automatically creates touchpoints, tasks, business opportunities, leads, call logs, and notes in the database. No typing required.

The MFD records a voice note, sees a pre-filled confirmation card with editable fields, taps confirm, and the entity is created. The entire flow takes 2-3 seconds for quick commands and 10-15 seconds for end-of-day brain dumps.

---

## Why voice

MFDs spend 30-45 minutes daily on data entry — logging calls, scheduling meetings, creating follow-up tasks. Most skip it entirely because typing on mobile is tedious. Voice input eliminates this friction. The MFD speaks naturally the way they already talk to colleagues, and the system handles the rest.

The app supports two input modes. A quick mic tap for single commands ("Rajesh Sharma se kal 3 baje milna hai, SIP review"), and a "Record day" button for end-of-day dumps where the MFD speaks for 3-10 minutes covering everything they did that day — meetings attended, calls made, follow-ups needed, new leads received.

---

## How it works — the complete flow

### Step 1: Record

The MFD opens the app and either taps the mic icon (quick command) or the "Record day" button (EOD dump). Flutter records audio in OGG/Opus format — small file size, high quality, natively supported by Gemini.

Before uploading, the app validates the recording on-device. File size must be under 5MB, duration under 10 minutes. A silence check prevents empty recordings from wasting API calls — if the audio is effectively silent, the app shows "We didn't hear anything — try again" without ever hitting the backend.

### Step 2: Upload and track

The app uploads the audio file to Supabase Storage under `voice-notes/{user_id}/{uuid}.ogg`. Then it inserts a tracking row into the `voice_inputs` table with `status: pending`. This row is the single source of truth for the entire pipeline — every stage reads from and writes to this row.

### Step 3: Enqueue

The app calls `POST /api/voice/enqueue` with the audio URL and the row ID. This endpoint returns immediately in about 100 milliseconds — it does not process the audio. It fires an async background task and responds with `status: queued`.

The app then subscribes to Supabase Realtime on that specific row, watching for status changes.

### Step 4: Process (background)

The background worker picks up the job behind a concurrency semaphore (max 10 simultaneous jobs). This prevents a burst of 200 users recording at once from overwhelming the Gemini API.

The worker does three things:

First, it queries Supabase for the user's client list — up to 100 recent clients with their name, phone, area, and AUM. This list will be injected into the prompt so Gemini can match spoken names like "Sharma ji" to actual client records.

Second, it builds a rich date/time context. Not just "current date is March 15" but the full picture: today is Saturday, here's the current week boundary (Mon-Sun), and here are the next 14 days listed by name and date. This context is what makes "next Friday" resolve to exactly March 20, 2026 instead of being ambiguous.

Third, it sends the raw audio bytes along with the system prompt, client list, and date context to Gemini 2.5 Flash in a single API call. Gemini processes the audio natively — it understands Hindi-English-Marathi code-switching directly from the audio signal without any separate speech-to-text step.

Gemini returns a JSON response containing a full English transcript of the audio and an array of extracted actions, each with an intent type, confidence score, entity fields, and any warnings.

The worker validates this JSON against a Pydantic schema (checking that intents are valid, confidence is between 0 and 1, required fields exist), then updates the tracking row to `status: needs_confirmation` with the parsed data.

### Step 5: Show confirmation

The moment the status changes to `needs_confirmation`, Supabase Realtime pushes the update to the Flutter app. What the app shows depends on how many actions were extracted.

For 1-3 actions (typical quick commands), the app shows individual confirmation cards. Each card displays the one-line summary ("Schedule meeting with Rajesh Sharma on Fri 20 Mar at 3 PM"), the pre-filled entity fields, and three buttons: Confirm, Edit, Discard.

For 4-20 actions (EOD dumps), the app shows a compact checklist. Each row has a checkbox, the intent badge (TOUCHPOINT, TASK, BO, etc.), a one-line summary, and a confidence percentage. High-confidence items (≥0.9) are pre-checked. Low-confidence items are flagged in amber. Tapping any row expands it to show the full editable fields.

Every field is editable with the appropriate widget: date picker for dates, time picker for times, client search dropdown for client names, fixed dropdowns for interaction type / priority / opportunity type, and free text fields for descriptions and notes.

### Step 6: Confirm

When the user taps Confirm (or "Confirm selected" for bulk), the app calls `POST /api/voice/confirm` for each confirmed action. The backend validates the entity fields, inserts into the correct Supabase table, queues a Google Calendar sync event if applicable, and updates the tracking row to `status: done`.

For bulk EOD confirms, the app iterates through checked action indices sequentially, showing progress ("Creating 8 of 11..."). Each action is independent — if action 3 fails, the other 10 still get created.

---

## The AI provider: Gemini 2.5 Flash

Gemini is the sole AI provider in the pipeline. It handles both speech understanding and intent extraction in a single API call. No separate speech-to-text service.

### Why Gemini over separate STT + LLM

The traditional approach (Sarvam/Deepgram for STT, then Claude/GPT for extraction) requires two API calls, two services to manage, two failure points, and costs 3x more. Gemini processes audio natively — it "listens" to the audio and extracts structured data directly, skipping the transcription-then-parse pipeline entirely.

At 1,000 users with 1 hour of audio each per month, Gemini costs approximately ₹19,600/month. The equivalent Sarvam + Claude setup costs ₹61,300/month. Gemini is both cheaper and simpler.

### How the Gemini call works

The backend downloads the audio bytes from Supabase Storage, then sends them to Gemini alongside a text prompt. The prompt contains three things:

The system instruction — a detailed schema defining every supported intent, its required and optional fields, matching rules for client names, date/time parsing rules for Hindi expressions, amount parsing rules for Indian number conventions, and the output JSON format.

The date context — dynamically computed per call. Includes the current date, day name, time, week boundaries, and a full 14-day calendar. This is what makes "next Friday" or "agle Monday" resolve to exact dates.

The client list — the user's recent clients with name, phone, area, and AUM bracket. This is what enables Gemini to match "Andheri wala Mishra" to the correct Sanjay Mishra when there are multiple Mishras in the database.

Gemini returns JSON with a transcript and an array of actions. Each action has an intent, confidence score, human-readable summary, entity fields, and warnings.

### What Gemini does NOT have

Zero database access. Gemini never sees a connection string, never runs a query, never touches the database. The FastAPI backend queries Supabase for the client list and date context, assembles it as plain text, and sends it to Gemini as part of the prompt. Gemini reads it like printed text and returns structured JSON. The backend then writes to the database using its own Supabase client.

---

## Smart features

### Date and time resolution

The system injects a full 14-day calendar into every Gemini call:

```
CURRENT DATE: 2026-03-15
CURRENT DAY: Saturday
CURRENT TIME: 16:30
CURRENT WEEK: Mon 09 Mar → Sun 15 Mar

NEXT 14 DAYS:
  Saturday 15 Mar 2026 ← TODAY
  Sunday 16 Mar 2026
  Monday 17 Mar 2026
  Tuesday 18 Mar 2026
  Wednesday 19 Mar 2026
  Thursday 20 Mar 2026
  Friday 21 Mar 2026
  Saturday 22 Mar 2026
  ...
```

When the MFD says "next Friday", Gemini literally sees Friday = 21 Mar 2026 in the list. No ambiguity. The prompt also defines Hindi date/time expressions: "kal" = tomorrow, "parso" = day after, "3 baje" = 15:00, "shaam ko" = 17:00, "dopahar" = 13:00.

If a resolved date is in the past, Gemini adds a `PAST_DATE` warning so Flutter can highlight the date field in amber.

### Client name matching

The prompt receives the user's client list with rich context:

```
KNOWN CLIENTS:
- Sanjay Mishra (id: uuid-2, phone: 9876543211, area: Andheri, AUM: ₹12,50,000)
- Sanjay Mishra (id: uuid-3, phone: 9999988888, area: Pune, AUM: ₹3,20,000)
- Deepak Mishra (id: uuid-4, phone: 8888877777, area: Bandra)
```

When the MFD says "Sanjay Mishra", Gemini detects two matches and returns a structured warning:

```json
{
  "client_id": null,
  "confidence": 0.72,
  "warnings": ["MULTIPLE_MATCH: Sanjay Mishra → uuid-2 (9876543211, Andheri), uuid-3 (9999988888, Pune)"]
}
```

Flutter parses the `MULTIPLE_MATCH` prefix and shows a dropdown picker: "Sanjay Mishra — 9876543211 (Andheri)" vs "Sanjay Mishra — 9999988888 (Pune)". The MFD taps the right one.

If the MFD says "Andheri wala Mishra", Gemini uses the area context to resolve it to uuid-2 with high confidence — no picker needed.

If the name doesn't match anyone, Gemini returns a `NO_MATCH` warning and Flutter shows a "Client not found — search or create" option.

### Multi-action extraction

A single voice note can contain multiple actions. If the MFD says:

"Rajesh Sharma se kal 3 baje milna hai SIP review ke liye, aur Priya Patel ko Friday tak term insurance statement bhejo, aur note to self HDFC NAV check karna morning meeting se pehle"

Gemini extracts three separate actions: a touchpoint with Rajesh, a task for Priya's statement, and a quick note about HDFC NAV. Each gets its own confirmation card (or checklist row in EOD mode).

The maximum is 20 actions per voice note.

### Amount parsing

Indian number conventions are handled natively: "25 thousand" or "25 hazar" = 25,000. "2 lakh" or "do lakh" = 2,00,000. "50 hazar" = 50,000. "5 crore" = 5,00,00,000. "10 lakh 50 hazar" = 10,50,000.

---

## Supported voice commands

### Schedule touchpoint

Example: "Rajesh Sharma se kal 3 baje milna hai, SIP portfolio review"

Creates a row in the `touchpoints` table with client, date, time, interaction type, and purpose. Queues Google Calendar sync.

Required: client (matched or named), date. Optional: time, type (meeting/call/video_call/review), location, purpose.

### Create task

Example: "Priya Patel ko Friday tak term insurance statement bhejo email pe"

Creates a row in the `tasks` table with description, due date, medium, and priority. Queues Google Calendar sync.

Required: description, due date. Optional: client, priority (low/medium/high/urgent), medium (call/email/whatsapp/visit), product type.

### Create business opportunity

Example: "Amit Desai ke saath new SIP opportunity, 25000 per month, follow up next week"

Creates a row in the `business_opportunities` table with client, opportunity type, expected amount, and due date. Queues Google Calendar sync.

Required: client, opportunity type, due date. Optional: expected amount, source, additional info.

Opportunity types: mutual_fund_sip, mutual_fund_lumpsum, insurance_life, insurance_health, insurance_pa, pms, aif, fixed_deposit, bonds, others.

### Add lead

Example: "Sharma ji ka colleague Vikram, IT mein kaam karta hai, around 35, Andheri mein rehta hai"

Creates a row in the `leads` table with name, source, and any demographic details mentioned.

Required: name. Optional: phone, email, area, age group, gender, occupation, income group, notes, scheduled date.

Sources: referral, cold_call, walk_in, social_media, website, event, existing_client, other.

### Log call

Example: "Abhi Meera se 15 minute baat hui, insurance renewal ke baare mein discuss kiya"

Creates a row in the `call_logs` table with client, call type, duration, and notes.

Required: client, call type. Optional: duration in seconds, notes.

### Quick note

Example: "Note to self — HDFC MF NAV update check karna morning meeting se pehle"

Creates a row in the `quick_notes` table with freeform content.

Required: content. Optional: tags.

---

## Confirmation UI

### Quick mode (1-3 actions)

Each action is shown as an individual card with pre-filled, editable fields:

```
┌─────────────────────────────────┐
│  TOUCHPOINT              94%    │
│                                 │
│  "Schedule meeting with Rajesh  │
│   Sharma on Fri 20 Mar at 3PM" │
│                                 │
│  Client   [Rajesh Sharma    ▼]  │  ← client dropdown
│  Type     [Meeting          ▼]  │  ← fixed options dropdown
│  Date     [Fri, 20 Mar 2026 📅] │  ← date picker
│  Time     [3:00 PM          🕐] │  ← time picker
│  Purpose  [SIP portfolio rev..] │  ← text field
│                                 │
│  [Confirm]    [Edit]   [Discard]│
│                                 │
│  ▼ Show transcript              │
└─────────────────────────────────┘
```

Fields are always visible and pre-filled. The MFD scans, sees everything looks right, taps Confirm. If one field is wrong, they tap that specific field and fix it.

If a `MULTIPLE_MATCH` warning exists on the client field, the dropdown is pre-populated with the matching clients showing phone and area for disambiguation. If a `NO_MATCH` warning exists, the field shows a search widget to find or create the client.

If a `PAST_DATE` warning exists, the date field is highlighted in amber with a note.

### EOD mode (4-20 actions)

A compact checklist where each row shows a checkbox, intent badge, one-line summary, and confidence:

```
☑  TOUCHPOINT  Meeting with Rajesh Sharma, Fri 20 Mar    94%
☑  TASK        Send statement to Priya Patel by Friday    91%
☑  BO          New SIP — Amit Desai ₹25,000/mo            89%
☐  TOUCHPOINT  Call with Sharma?                          62%
                ⚠ 3 clients named "Sharma" — tap to pick
☑  CALL LOG    15 min call with Meera                     95%
☑  NOTE        Check HDFC NAV before morning meeting      97%
+ 6 more actions                              [Show all]

──────────────────────────────────────────────
[Confirm selected (9)]            [Discard all]
```

High-confidence items (≥0.9) are pre-checked. Low-confidence items (<0.8) are unchecked and flagged in amber. Tapping any row expands it inline to show the full editable fields — same widgets as quick mode. The MFD can fix one field, collapse, check the next few, and hit "Confirm selected" at the bottom.

The raw transcript is available in a collapsible section at the bottom of both views. If Gemini missed something, the MFD can read the transcript and manually create the missed entry.

### What Flutter sends on confirm

When the user changes any field and taps Confirm, Flutter sends the complete entity with corrected values:

```json
{
  "user_id": "uuid",
  "voice_input_id": "uuid",
  "action_index": 0,
  "confirmed": true,
  "edited_entities": {
    "client_id": "uuid-2",
    "client_name": "Sanjay Mishra",
    "scheduled_date": "2026-03-20",
    "scheduled_time": "15:00",
    "interaction_type": "meeting",
    "purpose": "SIP portfolio review"
  },
  "idempotency_key": "flutter-generated-uuid"
}
```

If the user didn't edit anything, `edited_entities` is null and the backend uses the original values from Gemini's output.

For bulk confirms, Flutter calls the confirm endpoint once per checked action, showing progress.

---

## Production reliability

### Async processing

Nothing happens in the HTTP request path. The enqueue endpoint returns in 100ms. All Gemini calls run in background tasks behind a semaphore. The user sees "Processing..." for 2-10 seconds, which feels natural.

### Concurrency control

A semaphore limits to 10 concurrent Gemini calls. When 200 users record simultaneously, jobs beyond the limit queue up. Each user sees a few extra seconds of "Processing..." but no failures from API rate limiting.

### Retry with exponential backoff

Every Gemini call retries up to 3 times on transient failures: 1 second, then 2 seconds, then 4 seconds, with random jitter to prevent thundering herd. Only retries on timeouts and server errors (429, 500-504). Client errors (400, 401, 403) fail immediately.

### Circuit breaker

One circuit breaker for Gemini. After 5 consecutive failures, it trips to OPEN — subsequent requests fail instantly instead of waiting 15 seconds for a timeout. After 60 seconds it allows one test request. If that succeeds, it reopens. If not, it stays open for another 60 seconds.

### Fallback chain

When Gemini's circuit breaker is OPEN, the system automatically falls back to Sarvam STT (speech to text) followed by Claude Haiku (intent extraction). This costs 3x more but keeps the pipeline alive during Google outages. Sarvam and Claude API keys are optional — if not configured, fallback is disabled and the system degrades gracefully.

### Graceful degradation

If both Gemini AND the fallback fail, the system doesn't crash. It sets `status: needs_confirmation` with an "unknown" intent containing whatever transcript it managed to extract. The Flutter card shows: "Couldn't parse automatically — here's what you said: [transcript]" with an option to manually create the entity. The user still gets value from the transcription.

### Idempotency

Every confirm request carries a client-generated UUID. If the user double-taps Confirm, or if the network drops and Flutter retries, the backend sees the same key and returns the existing entity instead of creating a duplicate. This is critical for MFDs dealing with client money — a duplicate touchpoint is a nuisance, but a duplicate business opportunity could cause real problems.

### Input validation

Audio: max 5MB, max 10 minutes, allowed MIME types only, silence detection on device. Gemini output: JSON parse followed by Pydantic schema validation. Entity fields: client_id verified against user's actual client list, required fields checked per intent type. Confirm request: ownership verification (user_id must match), action_index bounds checking.

### Ownership check

Every endpoint verifies the requesting user_id matches the voice_inputs row. No user can see, confirm, or discard another user's voice commands.

### Data preservation

The audio file always remains in Supabase Storage regardless of pipeline success or failure. Even if everything crashes, the raw OGG file is there. A support engineer can replay the audio and manually enter the data.

---

## Observability

### Structured logging

Every log entry is JSON with a trace ID that flows through all pipeline stages:

```json
{"trace_id": "voice-abc12345", "stage": "gemini_audio", "status": "success", "duration_ms": 2100, "num_actions": 3}
{"trace_id": "voice-abc12345", "stage": "job", "status": "complete", "total_duration_ms": 2800}
```

Filter `trace_id = voice-abc12345` to see the complete lifecycle of a single voice command.

### Health endpoint

`GET /api/voice/health` returns circuit breaker states and queue capacity:

```json
{
  "status": "ok",
  "breakers": {
    "gemini": { "state": "CLOSED", "failure_count": 0, "threshold": 5 },
    "sarvam": { "state": "CLOSED", "failure_count": 0, "threshold": 5 },
    "claude": { "state": "CLOSED", "failure_count": 0, "threshold": 3 }
  },
  "queue_available": 8
}
```

Alert if any breaker is OPEN for more than 5 minutes. Alert if queue_available is 0 for more than 30 seconds.

### Quality metrics

The most important metric is user edit rate — how often MFDs modify fields before confirming. Track this by comparing `edited_entities` against original `parsed_data` in confirmed voice inputs.

If edit rate is under 15%, the system is working well. If edit rate is above 30%, the Gemini prompt needs tuning. Track which specific fields get edited most to pinpoint whether it's client name matching, date parsing, or intent classification that's weak.

---

## Database

### New table: voice_inputs

This is the only new table. The pipeline reads from existing tables (clients) and writes to existing tables (touchpoints, tasks, business_opportunities, leads, call_logs, quick_notes, calendar_event_queue).

```
voice_inputs
├── id                    uuid, primary key
├── user_id               uuid, FK to auth.users
├── audio_url             text, Supabase Storage URL
├── audio_duration_seconds numeric
├── audio_size_bytes      integer
├── input_mode            varchar ('quick' | 'eod')
├── status                varchar (pending | processing | needs_confirmation | done | discarded | failed)
├── transcript            text, English transcript from Gemini
├── parsed_data           jsonb, Gemini's full JSON output
├── error_message         text, populated on failure
├── retry_count           integer
├── created_entity_type   varchar, set on confirm
├── created_entity_id     uuid, set on confirm
├── processed_at          timestamptz, set on confirm/discard
├── idempotency_key       varchar, client-generated
├── trace_id              varchar, for log correlation
├── created_at            timestamptz
└── updated_at            timestamptz
```

### Status lifecycle

```
pending → processing → needs_confirmation → done
                    ↘                     ↗
                      failed    discarded
```

Each status is set by a specific actor: `pending` by Flutter on insert, `processing` and `needs_confirmation` by the background worker, `done` and `discarded` by the confirm endpoint, `failed` by the worker on error.

### Entity writer routing

The entity writer is config-driven. Each intent maps to a table, a set of required fields, optional fields with defaults, and whether calendar sync should be queued:

```
schedule_touchpoint  → touchpoints            + calendar sync
create_task          → tasks                  + calendar sync
create_bo            → business_opportunities + calendar sync
add_lead             → leads
log_call             → call_logs
quick_note           → quick_notes
```

Adding a new voice command type means adding a config block — no code changes. The writer reads the config, validates required fields, builds the insert payload, writes to the table, and optionally queues calendar sync.

Calendar sync is fire-and-forget. If the `calendar_event_queue` insert fails, it's logged but does not block entity creation.

---

## API reference

### POST /api/voice/enqueue

Accepts a voice input and starts async processing. Returns immediately.

Request:
```json
{
  "user_id": "uuid",
  "audio_url": "https://project.supabase.co/storage/v1/...",
  "voice_input_id": "uuid",
  "input_mode": "quick",
  "audio_size_bytes": 45000,
  "audio_duration_seconds": 18.5,
  "audio_mime_type": "audio/ogg",
  "idempotency_key": "uuid"
}
```

Response: `{"voice_input_id": "...", "status": "queued", "message": "..."}`

Errors: 429 (rate limited), 422 (validation failed)

### POST /api/voice/confirm

Confirms or discards a parsed action. Idempotent.

Request:
```json
{
  "user_id": "uuid",
  "voice_input_id": "uuid",
  "action_index": 0,
  "confirmed": true,
  "edited_entities": { "client_id": "uuid-2", "scheduled_date": "2026-03-20" },
  "idempotency_key": "uuid"
}
```

Response: `{"status": "created", "entity_type": "touchpoint", "entity_id": "uuid"}`

Errors: 404 (not found), 403 (not owner), 400 (invalid index / missing field / client not found)

### GET /api/voice/status/{voice_input_id}?user_id=uuid

Polling fallback if Realtime WebSocket drops. Returns current row data.

### GET /api/voice/health

Circuit breaker states and queue capacity for monitoring.

---

## Flutter integration summary

### Recording
Use `record` or `flutter_sound` package. OGG/Opus format. Quick mode auto-stops at 60 seconds. EOD mode allows up to 10 minutes. Check for silence before uploading.

### Upload + enqueue
Generate UUID → upload audio to Storage → insert `voice_inputs` row (status: pending) → call `/enqueue` → show "Processing..." indicator.

### Realtime subscription
Subscribe to `voice_inputs` table filtered by the row ID. On `needs_confirmation` → parse `parsed_data` and show the appropriate UI (card or checklist). On `failed` → show error with retry option.

### Polling fallback
If WebSocket disconnects, poll `GET /status/{id}` every 2 seconds until a terminal status is received.

### Confirmation
For each confirmed action, generate an idempotency key and call `/confirm`. Show green checkmark on success, error message on failure. For bulk confirm, iterate sequentially with progress indicator.

---

## Cost

### Gemini 2.5 Flash pricing

Audio input: $1.00 per million tokens (25 tokens per second of audio). Text input: $0.30 per million tokens. Text output: $2.50 per million tokens.

### Monthly estimates

| Users | Total audio | Monthly cost | Per user |
|-------|-------------|--------------|----------|
| 100 | 100 hours | ₹1,960 | ₹19.60 |
| 1,000 | 1,000 hours | ₹19,600 | ₹19.60 |
| 5,000 | 5,000 hours | ₹98,000 | ₹19.60 |
| 10,000 | 10,000 hours | ₹1,96,000 | ₹19.60 |

Assumption: 1 hour of audio per user per month. Linear scaling.

### Per-command cost

A 30-second quick command costs approximately ₹0.20. A 5-minute EOD dump costs approximately ₹1.50.

---

## Project structure

```
voice_workflow/
├── main.py                              # FastAPI entry point
├── config.py                            # All env vars + defaults
├── requirements.txt                     # 10 dependencies
├── .env.example                         # Template — fill 3 keys minimum
├── README.md
├── migrations/
│   └── 001_create_voice_inputs.sql      # Run in Supabase SQL Editor
├── controllers/
│   └── voice_controller.py              # 4 endpoints (thin, delegates to services)
├── services/
│   ├── gemini_service.py                # Primary: raw audio → structured JSON
│   ├── fallback.py                      # Sarvam + Claude (emergency only)
│   ├── entity_writer.py                 # Config-driven: intent → correct table
│   └── queue.py                         # Background worker with semaphore
├── models/
│   ├── enums.py                         # IntentType, VoiceInputStatus, InputMode
│   └── schemas.py                       # Pydantic validation for everything
├── prompts/
│   └── intent_extraction.py             # Gemini prompt + smart date/client context
└── utils/
    ├── circuit_breaker.py               # Per-service failure protection
    ├── retry.py                         # Exponential backoff + jitter
    ├── rate_limiter.py                  # 10 req/min per user
    ├── logger.py                        # Structured JSON with trace IDs
    └── db.py                            # Supabase client singleton
```

---

## Setup

1. Run `migrations/001_create_voice_inputs.sql` in Supabase SQL Editor
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`, fill in: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY`
4. Optional fallback keys: `SARVAM_API_KEY`, `ANTHROPIC_API_KEY`
5. Dev: `uvicorn voice_workflow.main:app --reload --port 8000`
6. Prod: `gunicorn voice_workflow.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`
7. Verify: `curl http://localhost:8000/api/voice/health`
