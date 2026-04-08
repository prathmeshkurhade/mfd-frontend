# 📋 **SHEETS SYNC - Implementation Phases Roadmap**

Complete step-by-step guide for implementing the bidirectional Google Sheets sync system.

---

## **PHASE 1: Setup & Configuration** ✓ (Prerequisites)

### 1.1 Google Cloud Project Setup
- [ ] Create Google Cloud Project (or use existing)
- [ ] Enable Google Sheets API v4
- [ ] Enable Google Drive API v3
- [ ] Create OAuth 2.0 credentials (Web Application)
  - Authorized redirect URIs: `https://your-supabase-instance.supabase.co/functions/v1/google-oauth-callback`
- [ ] Create Service Account for backend automation
- [ ] Download service account JSON key
- [ ] Keep credentials secure (use Supabase Secrets)

### 1.2 Supabase Configuration
- [ ] Create/Configure Supabase project
- [ ] Add Environment Secrets (Settings > Secrets):
  - `GOOGLE_CLIENT_ID` → from Google Cloud
  - `GOOGLE_CLIENT_SECRET` → from Google Cloud
  - `GOOGLE_SERVICE_ACCOUNT` → entire service account JSON as string
- [ ] Create required database tables:
  - `mfd_profiles` (if not exists)
  - `app_config` (if not exists)
  - `excel_sync_logs` (for tracking syncs)

### 1.3 Database Schema Creation
Run these migrations to add required columns:

```sql
-- Add Google OAuth columns to mfd_profiles
ALTER TABLE mfd_profiles ADD COLUMN IF NOT EXISTS google_connected boolean DEFAULT false;
ALTER TABLE mfd_profiles ADD COLUMN IF NOT EXISTS google_email text;
ALTER TABLE mfd_profiles ADD COLUMN IF NOT EXISTS google_access_token text;
ALTER TABLE mfd_profiles ADD COLUMN IF NOT EXISTS google_refresh_token text;
ALTER TABLE mfd_profiles ADD COLUMN IF NOT EXISTS google_token_expiry timestamp with time zone;
ALTER TABLE mfd_profiles ADD COLUMN IF NOT EXISTS google_drive_folder_id text;
ALTER TABLE mfd_profiles ADD COLUMN IF NOT EXISTS google_sheet_id text;
ALTER TABLE mfd_profiles ADD COLUMN IF NOT EXISTS google_clients_folder_id text;

-- Create app_config table if not exists
CREATE TABLE IF NOT EXISTS app_config (
  id bigserial PRIMARY KEY,
  key text UNIQUE NOT NULL,
  value text NOT NULL,
  description text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

-- Create excel_sync_logs table
CREATE TABLE IF NOT EXISTS excel_sync_logs (
  id bigserial PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id),
  sync_type text, -- 'lead', 'client', 'task', etc.
  sync_direction text, -- 'app_to_sheet' or 'sheet_to_app'
  records_synced integer DEFAULT 0,
  status text, -- 'success', 'failed', 'partial'
  error_message text,
  completed_at timestamp with time zone DEFAULT now(),
  duration_ms integer
);

-- Insert config values
INSERT INTO app_config (key, value, description) VALUES
('template_sheet_id', 'YOUR_TEMPLATE_SHEET_ID', 'Master template for user sheets'),
('google_service_account', '{...sa json...}', 'Service account for backend syncing')
ON CONFLICT (key) DO NOTHING;
```

---

## **PHASE 2: Edge Functions Deployment**

### 2.1 Deploy `google-oauth-start`
**What it does**: Initiates OAuth flow, redirects user to Google consent screen

Steps:
- [ ] Deploy function to Supabase (use provided code)
- [ ] Test OAuth URL generation
  ```bash
  curl "https://your-project.supabase.co/functions/v1/google-oauth-start?user_id=test-user-id"
  ```
- [ ] Verify redirect URI works correctly
- [ ] Test with actual Google account (not just service account)

### 2.2 Deploy `google-oauth-callback` ⭐ CRITICAL
**What it does**: Handles OAuth callback, stores tokens, AUTO-CREATES folder structure

Steps:
- [ ] Deploy function to Supabase
- [ ] **CRITICAL TEST**: Verify folder structure creation matches requirements:
  ```
  Google Drive Root:
  ├── ${userName} - My Sheets/
  │   └── ${userName} - Infinity Sheet (spreadsheet)
  └── ${userName} - Clients/
      ├── A/
      ├── B/
      ├── C/
      ... (through Z)
  ```
- [ ] Test token storage in `mfd_profiles` table
- [ ] Verify tokens are encrypted/secure
- [ ] Test error handling for:
  - Invalid auth code
  - Network failures
  - Already existing sheet
- [ ] Test success page displays correctly

### 2.3 Deploy `check-user-setup`
**What it does**: Returns user's sync status (connected/not connected)

Steps:
- [ ] Deploy function to Supabase
- [ ] Test checking sync status for authenticated user
- [ ] Verify response includes:
  - `google_connected` status
  - `google_email`
  - `google_sheet_url` (if connected)

### 2.4 Deploy `push-to-sheets`
**What it does**: Syncs app data to Google Sheets (triggered by database changes)

Steps:
- [ ] Deploy function to Supabase
- [ ] Test with sample API requests
- [ ] Verify Google Sheets API integration:
  - Service account JWT generation works
  - Token caching works
  - Sheet headers are read correctly
- [ ] Test column mapping (database columns → sheet columns)
- [ ] Test update vs. insert logic:
  - New record → appends row
  - Existing record → updates row
- [ ] Test performance (<2 sec per sync)
- [ ] Test error logging to `excel_sync_logs`

### 2.5 Deploy `sheets-webhook`
**What it does**: Receives edits from Google Apps Script, updates database

Steps:
- [ ] Deploy function to Supabase
- [ ] Configure webhook endpoint URL
- [ ] Set up CORS headers for Apps Script calls
- [ ] Test webhook signature validation
- [ ] Test data parsing from Apps Script payload
- [ ] Test database updates from sheet edits
- [ ] Add error recovery/retry logic

### 2.6 Deploy `create-user-sheet` (Manual Fallback)
**What it does**: Manual sheet creation if auto-creation fails

Steps:
- [ ] Deploy function to Supabase
- [ ] Test manual sheet creation endpoint
- [ ] Use as fallback if auto-creation fails
- [ ] Verify permission checks (user must be authenticated)

---

## **PHASE 3: Database Triggers Setup**

### 3.1 Create Trigger Functions
Create PostgreSQL function that calls edge function on data changes:

```sql
CREATE OR REPLACE FUNCTION public.trigger_generic_push_to_sheets()
RETURNS trigger AS $$
DECLARE
  request_body jsonb;
BEGIN
  -- Build the request payload
  request_body := jsonb_build_object(
    'id', COALESCE(NEW.id::text, OLD.id::text),
    'userId', COALESCE(NEW.user_id::text, OLD.user_id::text),
    'table', TG_TABLE_NAME,
    'rowData', to_jsonb(NEW) - 'user_id'
  );

  -- Call edge function asynchronously
  PERFORM pg_net.http_post(
    'https://your-project.supabase.co/functions/v1/push-to-sheets',
    request_body,
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.service_role_key')
    )
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 3.2 Attach Triggers to Tables
For each table that syncs to sheets (leads, clients, tasks, etc.):

```sql
CREATE TRIGGER trigger_leads_push_to_sheets
AFTER INSERT OR UPDATE ON leads
FOR EACH ROW
EXECUTE FUNCTION trigger_generic_push_to_sheets();

CREATE TRIGGER trigger_clients_push_to_sheets
AFTER INSERT OR UPDATE ON clients
FOR EACH ROW
EXECUTE FUNCTION trigger_generic_push_to_sheets();

-- Repeat for: tasks, communications, opportunities, etc.
```

### 3.3 Test Trigger Execution
- [ ] Insert test record: `INSERT INTO leads (user_id, name, phone) VALUES (...)`
- [ ] Verify trigger fires in Supabase logs
- [ ] Verify `push-to-sheets` function is called
- [ ] Verify record appears in Google Sheets within 2 seconds
- [ ] Check `excel_sync_logs` table for success entry

---

## **PHASE 4: Google Apps Script Setup**

### 4.1 Template Sheet Preparation
Create the master template sheet:

- [ ] Create new Google Sheet (this becomes the template)
- [ ] Add tabs (sheets) for each entity type:
  - `Leads` (for leads)
  - `Clients` (for clients)
  - `Tasks` (for tasks)
  - `Communications` (for emails/messages)
  - `Opportunities` (for business opportunities)
  - `Settings` (for configuration)
  - `Monitoring` (for logs/errors)
- [ ] Set up column headers matching database fields:
  ```
  Leads sheet headers:
  ID | Name | Email | Phone | Status | Source | Created | ...
  ```
- [ ] Apply professional formatting/styling
- [ ] Share with service account (read-only)
- [ ] **Save the sheet ID** → add to `app_config` table as `template_sheet_id`

### 4.2 Apps Script Installation
- [ ] Open sheet > Extensions > Apps Script
- [ ] Clear default code
- [ ] Copy provided Apps Script code (from `apps-script/Code.gs`)
- [ ] Update configuration:
  ```javascript
  const CONFIG = {
    WEBHOOK_URL: 'https://your-project.supabase.co/functions/v1/sheets-webhook',
    TABLES_TO_SYNC: ['Leads', 'Clients', 'Tasks', 'Communications'],
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY_MS: 1000
  };
  ```
- [ ] Deploy Apps Script (not just save)
- [ ] Set up triggers:
  - `onEdit` trigger (on sheet edit)
  - Time-based trigger for periodic checks

### 4.3 Apps Script Configuration
- [ ] Set webhook endpoint URL pointing to `sheets-webhook`
- [ ] Configure which sheets/tables to sync back to app
- [ ] Implement retry logic for failed syncs
- [ ] Add logging to "Monitoring" sheet
- [ ] Test with manual sheet edit

---

## **PHASE 5: Frontend Integration**

### 5.1 OAuth Connect Button
Add "Connect Google Sheets" button to user settings:

```typescript
// Backend endpoint: GET /google-oauth-start?user_id={id}
async function connectGoogleSheets() {
  const userId = getCurrentUser().id;
  const response = await fetch(
    `https://api.infinity.app/google-oauth-start?user_id=${userId}`
  );
  const { redirectUrl } = await response.json();
  window.location.href = redirectUrl;
}
```

Flow:
1. User clicks "Connect Google Sheets" button
2. Show loading spinner
3. Redirect to `/google-oauth-start`
4. User sees Google consent screen
5. User clicks "Allow"
6. Google redirects to callback
7. Callback creates folders + sheet
8. User redirected to success page
9. Frontend shows "✅ Connected!" with links to sheet

### 5.2 Status Display
In user dashboard/settings:

- [ ] Show connection status:
  - 🟢 Connected as: user@gmail.com
  - 🔴 Not connected
- [ ] Show last sync time
- [ ] Show sync health (healthy/errors)
- [ ] Add "Open Sheet" quick link (→ Google Sheets)
- [ ] Add "Open Drive" quick link (→ Clients folder)
- [ ] Add "Disconnect" button

### 5.3 Settings Page
Full sync management interface:

- [ ] Show connected email with verification
- [ ] Allow user to disconnect Google and revoke tokens
- [ ] Manual sync trigger button
- [ ] Show last 10 sync logs
- [ ] Display any errors
- [ ] Show sync statistics (% success, records synced, etc.)

---

## **PHASE 6: Testing & Validation**

### 6.1 Unit Tests
Test individual functions in isolation:

```typescript
// Test OAuth callback
test('oauth-callback: stores tokens correctly', async () => {
  const response = await callFunction('google-oauth-callback', {
    code: 'test-code',
    state: btoa(JSON.stringify({ userId: 'test-user' }))
  });
  expect(response.status).toBe(200);
  // Verify DB has tokens
});

// Test push-to-sheets
test('push-to-sheets: creates new row', async () => {
  const response = await callFunction('push-to-sheets', {
    id: 'lead-123',
    userId: 'user-123',
    table: 'leads',
    rowData: { name: 'John', email: 'john@test.com' }
  });
  expect(response.status).toBe(200);
});
```

- [ ] Test OAuth callback with mock Google responses
- [ ] Test token refresh logic
- [ ] Test folder creation logic
- [ ] Test Apps Script payload parsing
- [ ] Test column mapping logic
- [ ] **Target: 100% coverage for critical paths**

### 6.2 Integration Tests
Test systems working together:

- [ ] Complete OAuth flow with test Google account
- [ ] Folder creation and verification
- [ ] Token storage and retrieval
- [ ] Service account access to folders
- [ ] Template sheet copying
- [ ] App → sheet sync with real data
- [ ] Sheet → app sync with real edits
- [ ] Error recovery and retries

### 6.3 E2E Testing (Most Important!)
Complete user workflow:

1. [ ] Create test user account
2. [ ] Complete full OAuth flow
3. [ ] Verify folders created exactly as specified:
   - `testuser - My Sheets` folder ✓
   - `testuser - Clients` folder ✓
   - A-Z subfolders inside Clients ✓
   - Sheet inside My Sheets folder ✓
4. [ ] Create test lead in app (e.g., "John Doe")
5. [ ] Verify record appears in sheet within 2 seconds
6. [ ] Edit lead in sheet (e.g., change status to "Follow-up")
7. [ ] Verify update appears in app within 5 seconds
8. [ ] Edit in app, verify appears in sheet
9. [ ] Test all entity types (leads, clients, tasks, etc.)

### 6.4 Load Testing
Stress test the system:

- [ ] Simulate 100 concurrent users connecting
- [ ] Simulate 1000 records syncing simultaneously
- [ ] Monitor API rate limits (Google has quotas)
- [ ] Test quota handling and graceful degradation
- [ ] Performance targets:
  - OAuth flow: <3 seconds
  - Folder creation: <5 seconds
  - Each sync: <2 seconds
  - Webhook response: <1 second

### 6.5 Security Testing
Verify security measures:

- [ ] Unauthorized API calls are rejected
- [ ] Webhook signature validation works
- [ ] Token expiry is handled correctly
- [ ] Refresh token flow works
- [ ] Permission scopes are minimal and appropriate
- [ ] Service account can only access user's folders
- [ ] No sensitive data in logs

---

## **PHASE 7: Monitoring & Logging**

### 7.1 Set Up Logging Infrastructure
- [ ] Enable Supabase function logs (already available)
- [ ] Create `excel_sync_logs` table entries for all syncs
- [ ] Log structure:
  ```javascript
  {
    user_id: 'uuid',
    sync_type: 'lead',
    sync_direction: 'app_to_sheet',
    records_synced: 1,
    status: 'success',
    error_message: null,
    completed_at: '2026-01-29T14:30:45Z',
    duration_ms: 487
  }
  ```
- [ ] Add logging to all edge functions
- [ ] Log errors with full stack traces

### 7.2 Create Monitoring Dashboard
Build dashboard showing:

- [ ] Sync success rate (target: 99.9%)
- [ ] API quota usage (% of daily Google quota used)
- [ ] Error frequency and patterns
- [ ] Performance metrics (average sync time)
- [ ] Active users (currently syncing)
- [ ] Failed syncs (with error details)

### 7.3 Set Up Alerts
Configure alerts for:

- [ ] Failed OAuth (>1 failure per hour)
- [ ] Failed sheet creation (any failure)
- [ ] Repeated push failures (>3 failures in 1 hour)
- [ ] Webhook failures (rate >1% of requests)
- [ ] Google API quota nearing limit (>90%)
- [ ] Edge function errors (error rate >0.1%)

---

## **PHASE 8: Deployment & Launch**

### 8.1 Pre-Deployment Checklist
- [ ] All tests passing (unit, integration, E2E)
- [ ] Error handling in place for all failure scenarios
- [ ] Rate limiting configured
- [ ] Secrets properly configured in production
- [ ] Database backups enabled
- [ ] Monitoring/alerts configured and tested
- [ ] Rollback plan documented
- [ ] User documentation written
- [ ] Support team trained

### 8.2 Staging Deployment
- [ ] Deploy all edge functions to staging environment
- [ ] Deploy database migrations
- [ ] Run full smoke test suite
- [ ] Test complete OAuth flow with staging Google account
- [ ] Perform load test (realistic traffic)
- [ ] Test error scenarios

### 8.3 Production Deployment
- [ ] Get approval from stakeholders
- [ ] Deploy edge functions to production
- [ ] Deploy database migrations
- [ ] Deploy frontend changes
- [ ] Enable monitoring/alerts
- [ ] **Start with 10% user rollout**
  - Monitor error rates closely
  - Check sync success rate
  - Watch for performance issues
- [ ] If stable, **ramp up to 100% users**
  - Continue monitoring
  - Respond to user issues immediately
  - Have hotfix ready if needed

### 8.4 Launch Communication
- [ ] Write user-facing documentation
- [ ] Create tutorial videos showing:
  - How to connect Google Sheets
  - How to navigate sheet
  - How to make edits
  - How to troubleshoot
- [ ] Set up support channels
  - Email support
  - Help documentation
  - FAQ section
- [ ] Monitor user feedback
- [ ] Prepare rollback plan

---

## **PHASE 9: Post-Launch Maintenance**

### 9.1 Day 1-7: Close Monitoring
- [ ] Monitor sync success rate (target: 99.9%)
- [ ] Watch for error patterns
- [ ] Respond to user issues within 1 hour
- [ ] Fix critical bugs immediately
- [ ] Check logs for any anomalies

### 9.2 Week 2-4: Optimization
- [ ] Analyze performance data
- [ ] Optimize slow endpoints
- [ ] Improve error messages for users
- [ ] Fine-tune retry logic
- [ ] Gather user feedback
- [ ] Document lessons learned

### 9.3 Month 2+: Feature Enhancements
- [ ] Add support for more entity types (if needed)
- [ ] Implement selective sync (user chooses what syncs)
- [ ] Add conflict resolution for simultaneous edits
- [ ] Implement audit trail
- [ ] Add backup/restore capabilities
- [ ] Improve sheet formatting options

---

## **🎯 Critical Success Criteria**

| Metric | Target | How to Measure |
|--------|--------|-----------------|
| OAuth Success Rate | 99%+ | (successful logins) / (total login attempts) |
| Folder Creation | 100% success | Manual verification of folder structure |
| App → Sheet Sync Time | <2 seconds | Monitor from DB insert to sheet update |
| Sheet → App Sync Time | <5 seconds | Monitor from sheet edit to DB update |
| Sync Success Rate | 99.9%+ | (successful syncs) / (total syncs) |
| Data Accuracy | 100% | Spot checks, data validation |
| Uptime | 99.95%+ | Downtime minutes per month <22 min |
| User Satisfaction | 4.5+/5 stars | Post-launch survey |

---

## **📊 Current Status Tracker**

Update this as you progress:

- **Phase 1**: ⏳ [Pending] - Awaiting Google Cloud project setup
- **Phase 2**: ⏳ [Pending] - Code ready, waiting for deployment
- **Phase 3**: ⏳ [Pending] - Need database trigger implementation
- **Phase 4**: ⏳ [Pending] - Need Apps Script development
- **Phase 5**: ⏳ [Pending] - Need frontend button implementation
- **Phase 6**: ⏳ [Pending] - Ready for testing
- **Phase 7**: ⏳ [Pending] - Monitoring setup
- **Phase 8**: 🔜 [Not Started] - Launch phase
- **Phase 9**: 🔜 [Not Started] - Post-launch

---

## **Next Immediate Actions**

**TODAY:**
1. [ ] Confirm Google Cloud project created with correct APIs enabled
2. [ ] Confirm Supabase project configured with secrets
3. [ ] Run database migrations to create required columns
4. [ ] Deploy Phase 2 edge functions

**THIS WEEK:**
5. [ ] Create template Google Sheet
6. [ ] Deploy Phase 3 database triggers
7. [ ] Install Apps Script on template sheet
8. [ ] Begin Phase 6 testing

**NEXT WEEK:**
9. [ ] Complete all E2E tests
10. [ ] Deploy to staging
11. [ ] Begin frontend integration
12. [ ] Final security audit

---

**Questions?** Check [DETAILED_WORKING.md](./DETAILED_WORKING.md) for architecture details.
