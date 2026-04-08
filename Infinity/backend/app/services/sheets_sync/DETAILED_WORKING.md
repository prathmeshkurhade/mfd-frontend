# 📚 **Sheets Sync Service - Detailed Working Explained**

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INFINITY CRM SYSTEM                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐                    ┌──────────────────────┐  │
│  │   FastAPI App    │                    │  Google Sheets API   │  │
│  │   (Python)       │                    │  (External Service)  │  │
│  └────────┬─────────┘                    └──────────┬───────────┘  │
│           │                                         │              │
│           │ INSERT/UPDATE                           │ Edit rows    │
│           ▼                                         │              │
│  ┌──────────────────┐                               │              │
│  │  PostgreSQL DB   │◄──────────────────────────────┘              │
│  │  (main data)     │                                              │
│  └────────┬─────────┘                                              │
│           │                                                        │
│    DB Trigger: INSERT/UPDATE                                       │
│    ↓                                                               │
│  ┌──────────────────────────────────────────────────────┐         │
│  │  SUPABASE EDGE FUNCTIONS (Deno/TypeScript)           │         │
│  │  ┌─────────────────────────────────────────────────┐ │         │
│  │  │ 1. google-oauth-start                           │ │         │
│  │  │    → Redirects to Google OAuth consent          │ │         │
│  │  ├─────────────────────────────────────────────────┤ │         │
│  │  │ 2. google-oauth-callback                        │ │         │
│  │  │    → Stores tokens                              │ │         │
│  │  │    → Auto-creates folder + sheet                │ │         │
│  │  ├─────────────────────────────────────────────────┤ │         │
│  │  │ 3. check-user-setup                             │ │         │
│  │  │    → Returns user's sync status                 │ │         │
│  │  ├─────────────────────────────────────────────────┤ │         │
│  │  │ 4. push-to-sheets (DB Trigger)                  │ │         │
│  │  │    → Reads app data                             │ │         │
│  │  │    → Pushes to Google Sheets                    │ │         │
│  │  ├─────────────────────────────────────────────────┤ │         │
│  │  │ 5. sheets-webhook (Webhook)                     │ │         │
│  │  │    → Receives edits from Google Apps Script     │ │         │
│  │  │    → Updates database                           │ │         │
│  │  ├─────────────────────────────────────────────────┤ │         │
│  │  │ 6. create-user-sheet (Manual)                   │ │         │
│  │  │    → Manual sheet creation fallback             │ │         │
│  │  └─────────────────────────────────────────────────┘ │         │
│  └──────────────────────────────────────────────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 **Complete Data Flow**

### **Flow 1: User Connects Google (OAuth)**

```
1. User clicks "Connect Google Sheets"
   ↓
2. Frontend calls: GET /google-oauth-start?user_id=UUID
   ↓
3. Edge Function: google-oauth-start/index.ts
   ├─ Takes user_id from query param
   ├─ Reads GOOGLE_CLIENT_ID from Supabase Secrets
   ├─ Builds OAuth URL with scopes: drive, sheets, userinfo
   ├─ Returns HTTP 302 redirect
   ↓
4. Browser redirects to Google consent screen
   │
   User clicks "Allow"
   │
   ↓
5. Google redirects to: https://supabase.co/functions/v1/google-oauth-callback?code=AUTH_CODE&state=STATE
   ↓
6. Edge Function: google-oauth-callback/index.ts
   ├─ Validates state parameter (contains user_id)
   ├─ Exchanges auth code for access/refresh tokens
   │  POST https://oauth2.googleapis.com/token with:
   │  ├─ code (from Google)
   │  ├─ client_id (GOOGLE_CLIENT_ID)
   │  ├─ client_secret (GOOGLE_CLIENT_SECRET)
   ├─ Gets user email from Google userinfo endpoint
   ├─ Stores tokens in mfd_profiles:
   │  ├─ google_connected = true
   │  ├─ google_email = user@gmail.com
   │  ├─ google_access_token = abc123...
   │  ├─ google_refresh_token = def456...
   │  ├─ google_token_expiry = 2026-01-30 15:00:00
   ├─ Gets template sheet ID from app_config table
   ├─ Creates folder structure in user's Google Drive:
   │  └─ My Sheets/
   │     ├─ Clients/
   │     │  ├─ A/
   │     │  ├─ B/
   │     │  └─ ... (Z)
   │     └─ Tasks/
   ├─ Copies template sheet to "My Sheets" folder
   ├─ Saves sheet ID to mfd_profiles.google_sheet_id
   ├─ Returns HTML success page with:
   │  ├─ Sheet URL
   │  ├─ Folders URL
   │  ├─ Success confirmation
   ↓
7. User sees "✅ Sheet Created Successfully!"
```

---

### **Flow 2: App Data → Google Sheets (Automatic)**

```
1. Backend creates/updates a Lead record
   INSERT INTO leads (user_id, name, phone, email, ...) VALUES (...)
   ↓
2. PostgreSQL Trigger: trigger_generic_push_to_sheets()
   ├─ Fires on: AFTER INSERT OR UPDATE on leads table
   ├─ Collects: id, user_id, name, phone, email, status, ...
   ├─ Calls pg_net.http_post (Postgres networking extension)
   │  POST https://supabase.co/functions/v1/push-to-sheets
   │  Headers: Authorization: Bearer SERVICE_ROLE_KEY
   │  Body: {
   │    "id": "lead-uuid",
   │    "userId": "user-uuid",
   │    "table": "leads",
   │    "rowData": {
   │      "name": "John Doe",
   │      "phone": "9999999999",
   │      "email": "john@example.com",
   │      ...
   │    }
   │  }
   ↓
3. Edge Function: push-to-sheets/index.ts
   ├─ Validates auth header (SERVICE_ROLE_KEY)
   ├─ Gets user's google_sheet_id from mfd_profiles
   ├─ Maps table name: leads → "Leads" (sheet tab name)
   ├─ Gets Google service account from app_config
   ├─ Generates JWT signed by service account private key
   ├─ Exchanges JWT for Google access token (with caching)
   ├─ Reads sheet headers from first row:
   │  Headers: ["Name", "Phone", "Email", "Status", "Source", ...]
   ├─ Maps database columns to sheet columns:
   │  ├─ name → "Name"
   │  ├─ phone → "Phone"
   │  ├─ email → "Email"
   │  ├─ status → "Status"
   │  ├─ source → "Source"
   ├─ Searches existing sheet for matching row (by Name + Phone)
   ├─ If found: Updates row with new values
   ├─ If not found: Appends new row
   ├─ Calls Google Sheets API v4:
   │  PUT https://sheets.googleapis.com/v4/spreadsheets/{sheetId}/values/{range}
   ├─ Logs result to excel_sync_logs table:
   │  {
   │    "user_id": "...",
   │    "sync_type": "lead",
   │    "sync_direction": "app_to_sheet",
   │    "records_synced": 1,
   │    "status": "success",
   │    "completed_at": "2026-01-29 14:30:45"
   │  }
   ↓
4. Google Sheets Updated Instantly
   ├─ User sees new/updated row in sheet
   ├─ No manual refresh needed
```

**Performance:** <2 seconds per sync (usually <500ms)

---

### **Flow 3: Google Sheets → App Data (Webhook)**

```
1. User edits a row in Google Sheets
   │
   ├─ Edits "Status" of "John Doe" from "New" to "Follow-up"
   │
   ↓

2. Google Apps Script onEdit Trigger fires
   ├─ Detects: Leads sheet, Row 5, Column C changed
   ├─ Collects all current data:
   │  {
   │    "sheetId": "abc123...sheet-id",
   │    "sheetName": "Leads",
   │    "rows": [
   │      {
   │        "id": "lead-uuid",
   │        "name": "John Doe",
   │        "phone": "9999999999",
   │        "email": "john@example.com",
   │        "status": "Follow-up",  // CHANGED
   │        "source": "Referral",
   │        ...
   │      }
   │    ],
   │    "timestamp": "2026-01-29T14:35:00Z",
   │    "changeType": "edit"
   │  }
   ├─ Calls webhook:
   │  POST https://supabase.co/functions/v1/sheets-webhook
   │  Headers: x-webhook-secret: super_secret_key_123
   │  Body: { ...above JSON... }
   ↓

3. Edge Function: sheets-webhook/index.ts
   ├─ Validates webhook secret (prevents spoofing):
   │  GET app_config WHERE key = 'sheet_webhook_secret'
   │  Compare: x-webhook-secret header == app_config.value
   ├─ Finds user by sheet ID:
   │  SELECT user_id FROM mfd_profiles WHERE google_sheet_id = 'abc123'
   ├─ Maps sheet name to table:
   │  "Leads" → leads table
   │  "Client Profile" → clients table
   │  "Business Opportunities" → business_opportunities table
   ├─ Parses and transforms data:
   │  ├─ Converts strings to appropriate types
   │  ├─ Handles dates (YYYY-MM-DD → date)
   │  ├─ Handles numbers (Phone as string, Amount as decimal)
   │  ├─ Converts emails to lowercase
   ├─ Syncs leads (specialized logic):
   │  ├─ If row has "id" column: UPDATE leads SET ... WHERE id = ...
   │  ├─ If row has "name": INSERT new lead with generated UUID
   │  ├─ Handles duplicates: Check by (user_id, name, phone)
   ├─ Logs to excel_sync_logs:
   │  {
   │    "user_id": "...",
   │    "sync_type": "lead",
   │    "sync_direction": "sheet_to_app",
   │    "records_synced": 1,
   │    "status": "success",
   │    "completed_at": "2026-01-29 14:35:15"
   │  }
   ↓

4. PostgreSQL Updated
   ├─ Lead with id=uuid has status = "Follow-up" now
   ├─ Database triggers for this UPDATE don't fire (prevent loop)
   │  (Need to prevent push-to-sheets being called again)
   ↓

5. FastAPI App Gets Updated Data
   ├─ Next time leads are fetched, they have new status
   ├─ Frontend refreshes and shows updated data
```

---

## 🔐 **Authentication & Security**

### **Three Auth Levels**

```
1. USER OAUTH (User's own Google account)
   ├─ For: Creating folders in user's Drive
   ├─ Token: access_token + refresh_token
   ├─ Stored in: mfd_profiles (encrypted at rest)
   ├─ Used by: google-oauth-callback, create-user-sheet
   │
   Refresh Flow:
   ├─ Check if google_token_expiry < NOW()
   ├─ If expired: POST with refresh_token to Google
   ├─ Get new access_token
   ├─ Update google_token_expiry in DB

2. SERVICE ACCOUNT (Shared system account)
   ├─ For: Pushing data to sheets (doesn't need user confirmation)
   ├─ Auth: JWT signed with private key (RSA)
   ├─ Stored in: app_config (as JSON)
   ├─ Used by: push-to-sheets, data modifications
   │
   JWT Flow:
   ├─ Load service account JSON (has private_key)
   ├─ Create JWT claim: {"iss": service_account_email, "scope": "sheets API", "exp": now+3600}
   ├─ Sign with private key
   ├─ Exchange JWT for access_token from Google
   ├─ Cache token for 1 hour (reuse same token)
   ├─ Use token in API calls

3. SUPABASE SERVICE ROLE
   ├─ For: Backend server operations
   ├─ Auth: Service role key (password-like)
   ├─ Stored in: Supabase Secrets
   ├─ Used by: DB operations, verifying requests
   │
   Usage:
   ├─ Database queries (read/write with RLS bypass)
   ├─ Verifying incoming requests from triggers
   ├─ Creating/updating config tables
```

---

## 📊 **Data Transformation & Mapping**

### **Column Name Mapping Strategy**

When syncing, the system handles multiple naming conventions:

```typescript
// Sheet Header: "Contact No"
// Database has: phone

// Mapping logic tries (in order):
1. Exact match: rowData["Contact No"] → ❌ not found
2. Lowercase: rowData["contact no"] → ❌ not found
3. Underscore: rowData["contact_no"] → ❌ not found
4. Return empty string and skip this column

// OR (reverse direction)
// Database field: "phone"
// Sheet headers: ["Name", "Phone", "Contact No", "Mobile", ...]

// Try to find matching header:
1. Exact: headers.includes("phone") → ❌
2. Lowercase: headers.map(h => h.toLowerCase()).includes("phone") → ✅ "Phone"
3. Use header's position in array
```

---

### **Type Conversions**

```javascript
// Dates
"2026-01-29" → Date (YYYY-MM-DD format)
"01/29/2026" → Parsed and normalized

// Numbers
"1000000" → Parsed to numeric
"10,00,000" (Indian format) → Parsed to 1000000

// Booleans
"Yes" / "No" → true / false
"True" / "False" → true / false

// Decimals
"1000.50" → 1000.50
"1000" → 1000 (no decimal needed)

// Nulls
Empty cell → null
"N/A" → null
undefined → null
```

---

## 🔄 **Database Schema Integration**

### **Key Tables**

```sql
-- Your existing tables
leads
├─ id (UUID)
├─ user_id (FK → auth.users)
├─ name
├─ phone
├─ email
├─ status (follow_up, converted, rejected)
├─ source (referral, campaign, web, etc.)
└─ created_at

clients
├─ id (UUID)
├─ user_id (FK → auth.users)
├─ name
├─ phone
├─ email
├─ area
├─ birthdate
├─ gender
├─ occupation
├─ created_at

tasks
├─ id (UUID)
├─ user_id (FK → auth.users)
├─ description
├─ due_date
├─ status (pending, completed)
├─ priority (high, medium, low)

business_opportunities
├─ id (UUID)
├─ user_id (FK → auth.users)
├─ expected_amount
├─ opportunity_stage
├─ due_date

-- Sync Infrastructure (in sheets_sync)
mfd_profiles (YOUR EXISTING TABLE - ENHANCED)
├─ user_id (FK → auth.users)
├─ google_connected (boolean)
├─ google_email
├─ google_access_token (encrypted)
├─ google_refresh_token (encrypted)
├─ google_token_expiry
├─ google_sheet_id
├─ google_drive_folder_id
├─ google_clients_folder_id

app_config (CREATE THIS)
├─ key (unique) → "google_service_account", "sheet_webhook_secret", etc.
├─ value → actual secret/config

excel_sync_logs (YOUR EXISTING TABLE)
├─ user_id
├─ sync_type → "lead", "client", "task", "opportunity"
├─ sync_direction → "app_to_sheet" or "sheet_to_app"
├─ records_synced
├─ status → "success", "failed", "partial"
├─ error_message
├─ started_at
├─ completed_at
```

---

## 🎯 **Edge Function Responsibilities**

```
┌─ google-oauth-start ─────────────────────────────┐
│ Job: Gateway to OAuth flow                       │
│ Input: user_id (query param)                     │
│ Process:                                          │
│  1. Read GOOGLE_CLIENT_ID from secrets           │
│  2. Build OAuth URL with scopes                  │
│  3. Return 302 redirect                          │
│ Output: HTTP redirect to Google                  │
│ Failures: Missing GOOGLE_CLIENT_ID               │
└─────────────────────────────────────────────────┘

┌─ google-oauth-callback ──────────────────────────┐
│ Job: Complete OAuth flow & auto-create sheet    │
│ Input: code, state from Google                   │
│ Process:                                          │
│  1. Validate state (contains user_id)            │
│  2. Exchange code for tokens                     │
│  3. Get user email from Google                   │
│  4. Store tokens in mfd_profiles                 │
│  5. Create folder structure in Drive             │
│  6. Copy template sheet                          │
│ Output: HTML success/error page                  │
│ Failures: Invalid code, missing template sheet   │
└─────────────────────────────────────────────────┘

┌─ check-user-setup ───────────────────────────────┐
│ Job: Return user's sync readiness status        │
│ Input: JWT (Authorization header)                │
│ Process:                                          │
│  1. Extract user from JWT                        │
│  2. Check mfd_profiles for google_connected     │
│  3. Check for google_sheet_id                   │
│ Output: {                                        │
│   status: "ready" | "setup_required",            │
│   google_email: "...",                           │
│   oauth_url: "...",                              │
│   sheet_id: "..."                                │
│ }                                                │
└─────────────────────────────────────────────────┘

┌─ push-to-sheets ─────────────────────────────────┐
│ Job: Push app data to Google Sheets              │
│ Input: DB trigger (pg_net POST)                  │
│ Process:                                          │
│  1. Validate SERVICE_ROLE_KEY                    │
│  2. Get user's sheet ID & service account       │
│  3. Generate JWT & get Google access token      │
│  4. Read sheet headers                           │
│  5. Map DB columns to sheet columns             │
│  6. Find existing row or append new             │
│  7. Update Google Sheets API                    │
│  8. Log to excel_sync_logs                      │
│ Output: success/error response                  │
│ Failures: No sheet, service account error       │
└─────────────────────────────────────────────────┘

┌─ sheets-webhook ─────────────────────────────────┐
│ Job: Sync Google Sheets edits back to app       │
│ Input: Webhook from Google Apps Script           │
│ Process:                                          │
│  1. Validate webhook secret                      │
│  2. Find user by sheet ID                        │
│  3. Map sheet name to DB table                   │
│  4. Transform and parse data                     │
│  5. Run sync function (leads, clients, tasks)   │
│  6. Log to excel_sync_logs                      │
│ Output: {success: true, synced_count: X}        │
│ Failures: Invalid secret, unknown sheet         │
└─────────────────────────────────────────────────┘

┌─ create-user-sheet ──────────────────────────────┐
│ Job: Manual sheet creation (fallback)            │
│ Input: JWT (user's own token)                    │
│ Process:                                          │
│  1. Validate JWT                                  │
│  2. Check if user already has sheet             │
│  3. Load stored OAuth tokens                    │
│  4. Refresh token if expired                    │
│  5. Create folder structure (user's own Drive)  │
│  6. Copy template sheet                         │
│  7. Save sheet ID to DB                         │
│ Output: {sheet_url, folder_urls}                │
│ Failures: Tokens expired, no template           │
└─────────────────────────────────────────────────┘
```

---

## ⚙️ **Configuration & Secrets**

### **Environment Variables (Supabase Secrets)**

```bash
# Google OAuth (OAuth Client)
GOOGLE_CLIENT_ID=xxx-xxx-xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx

# Supabase (auto-set)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbG...xxxxx
SUPABASE_ANON_KEY=eyJhbG...xxxxx
```

### **Database Config (app_config Table)**

```sql
-- Key-value pairs stored in database
'google_service_account' → {"type":"service_account","project_id":"...","private_key":"-----BEGIN..."}
'template_sheet_id' → '1aBcDeFgHiJkLmNoPqRsTuVwXyZ'
'sheet_webhook_secret' → 'sup3r_s3cr3t_webhook_key_1234'
'supabase_url' → 'https://your-project.supabase.co'
```

---

## 🚨 **Error Handling & Recovery**

```
OAuth Errors:
├─ User denies permission → Show error page
├─ Invalid code → Show error page
├─ Token exchange fails → Log & show error
├─ Service account missing → Log critical

Push Errors:
├─ Sheet not found → Log, retry later
├─ Google API rate limit → Exponential backoff
├─ Invalid token → Refresh & retry
├─ Headers not found → Log schema mismatch

Webhook Errors:
├─ Invalid secret → 401 Unauthorized
├─ Sheet not registered → 404 Not Found
├─ DB write fails → 500 Internal Error
├─ Schema mismatch → Log & skip field
```

---

## 📈 **Performance Optimization**

```typescript
// Token Caching
Google access tokens valid for 1 hour
Edge function caches token in memory
Avoids redundant JWT generation

// Batch Syncing
Sheet webhook can handle multiple rows at once
Single function call = multiple record updates

// Column Header Caching
First call: Reads headers from sheet
Second call: Uses cached headers
Avoids redundant API calls

// Index Strategy
mfd_profiles → Index on user_id & google_sheet_id
excel_sync_logs → Index on user_id & completed_at
app_config → Primary key on key field
```

---

## 🔄 **Idempotency & Deduplication**

```
Problem: What if push-to-sheets is called twice?

Solution: Row Matching
├─ Find existing row by: name + phone combination
├─ If found: UPDATE (not INSERT)
├─ If not found: INSERT new row
└─ Result: No duplicates even with retries

Problem: What if webhook is sent twice from Apps Script?

Solution: Webhook timestamp + tracking
├─ Check excel_sync_logs for recent syncs
├─ If sync completed < 5 seconds ago with same timestamp
├─ Skip processing (prevent double updates)
```

---

## 📊 **Monitoring & Debugging**

### **View All Syncs**
```sql
SELECT * FROM excel_sync_logs 
ORDER BY completed_at DESC 
LIMIT 20;
```

### **View Failed Syncs**
```sql
SELECT * FROM excel_sync_logs 
WHERE status = 'failed' 
ORDER BY completed_at DESC;
```

### **Check User Status**
```sql
SELECT 
  user_id,
  google_connected,
  google_email,
  google_sheet_id
FROM mfd_profiles 
WHERE user_id = 'UUID';
```

### **Edge Function Logs**
```
Supabase Dashboard
→ Functions
→ Select function
→ Logs tab
→ View real-time execution logs
```

---

## 🎯 **Key Takeaway**

The sheets sync service is a **event-driven, bidirectional sync system**:

1. **User Setup**: OAuth → Auto sheet creation
2. **App → Sheet**: DB trigger → Edge function → Google Sheets (automatic)
3. **Sheet → App**: Google Apps Script → Webhook → Edge function → Database
4. **Configuration**: Secrets + app_config table + mfd_profiles columns
5. **Security**: JWT signing, webhook validation, service role auth
6. **Reliability**: Error logging, retry logic, idempotency

Everything is designed to be **automatic, secure, and user-friendly**.
