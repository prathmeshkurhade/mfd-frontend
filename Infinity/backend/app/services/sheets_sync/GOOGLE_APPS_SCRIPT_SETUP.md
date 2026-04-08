# Phase 4: Google Apps Script Setup

## Overview
Google Apps Script enables the **Sheets → Database** sync direction. When users edit cells in Google Sheets, it automatically calls the `sheets-webhook` edge function to update the database.

## Installation Steps

### 1. Open Google Sheet in Browser
- Navigate to your Google Sheet (the one created via OAuth)
- Verify it has these tabs: "Leads", "Client Profile", "Business Opportunities", "Dashboard"

### 2. Open Apps Script Editor
- Click **Extensions** → **Apps Script** in the menu
- This opens the Google Apps Script editor in a new tab

### 3. Replace Default Code
- Delete all existing code in `Code.gs` (default file)
- Copy entire content from [Code.gs](../app/services/sheets_sync/Code.gs)
- Paste into the editor

### 4. Set Webhook Secret
The script needs the webhook secret from your database.

**Option A: Manual Setup (Recommended)**
1. Go to Supabase Dashboard → SQL Editor
2. Run: 
   ```sql
   SELECT value FROM app_config WHERE key = 'sheet_webhook_secret';
   ```
3. Copy the secret value
4. In Apps Script editor, find this line (around line 6):
   ```javascript
   const WEBHOOK_SECRET = ''; // Get this from app_config table
   ```
5. Replace with:
   ```javascript
   const WEBHOOK_SECRET = 'your-secret-here';
   ```
6. Click **Save**

**Option B: Automatic Setup (Advanced)**
1. In Apps Script editor, click **Run** next to `setupWebhookSecret()` function
2. Paste the secret when prompted
3. Secret is saved to script properties

### 5. Test the Setup
1. In Apps Script editor, click **Run** next to `testWebhook()` function
2. Check **Execution log** at bottom for success message
3. Should see: `"Webhook sync successful"`

### 6. Enable Auto-Trigger (Optional but Recommended)
Google Apps Script should auto-detect the `onEdit` trigger. Verify:
1. Click **Triggers** (⏰ icon) on left sidebar
2. Should see: `onEdit` → `Head deployment`
3. If not present, add manually:
   - Click **Create new trigger**
   - Select function: `onEdit`
   - Event type: `On edit`
   - Click **Save**

## How It Works

### When User Edits a Cell:
1. `onEdit()` trigger fires automatically
2. Script captures entire row data (all columns)
3. Creates JSON payload with:
   - `sheetId`: Google Sheet ID
   - `sheetName`: Tab name (e.g., "Leads")
   - `rows`: Array with edited row data
   - `timestamp`: When edit happened
   - `changeType`: "edit"
4. Sends to `sheets-webhook` edge function via HTTPS
5. Webhook validates and updates database

### Security:
- Webhook secret validates request authenticity
- Only your authenticated users can trigger syncs
- Errors logged but don't block user edits

## Monitoring & Debugging

### View Execution Logs:
1. In Apps Script, click **Executions** (⏱️ icon) on sidebar
2. See all triggers that ran and their status

### Common Issues:

**Issue: "WEBHOOK_SECRET not configured"**
- Solution: Follow Step 4 above to set the secret

**Issue: "Webhook error" in logs**
- Check webhook secret matches `app_config` value
- Verify `WEBHOOK_URL` is correct for your Supabase project

**Issue: Some cells don't sync**
- Script only syncs complete rows (Row 2+)
- Header row (Row 1) is skipped
- Ensure no empty header cells

## What Syncs

Currently syncs from:
- **Leads** sheet → `leads` table
- **Client Profile** sheet → `clients` table
- **Business Opportunities** sheet → `business_opportunities` table
- **Dashboard** → Read-only (not synced)

## Testing Full Bidirectional Sync

1. **Test DB → Sheets (Database Triggers):**
   - Add lead in app
   - Check if it appears in "Leads" sheet

2. **Test Sheets → DB (Apps Script):**
   - Edit a cell in Google Sheet
   - Wait 2-3 seconds
   - Check in app if change was saved

3. **Test Error Handling:**
   - Edit with incomplete data (if required fields have validation rules)
   - Check if error logged but sheet still editable

## Next Steps

Once testing confirms both directions working:
- Phase 5: Frontend integration (React components for sync status)
- Phase 6: Advanced features (conflict resolution, audit logs)
- Phase 7: Production deployment & monitoring
