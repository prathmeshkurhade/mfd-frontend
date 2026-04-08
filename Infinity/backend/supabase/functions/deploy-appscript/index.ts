// ============================================================
// EDGE FUNCTION: deploy-appscript
// Deploys Code.gs to user's copied sheet using their OAuth token
// Called by user after OAuth login (via success page button)
// ============================================================

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// The actual Code.gs content to deploy
const CODE_GS_CONTENT = `// ============================================================
// INFINITY SYNC - Google Apps Script
// Enables bidirectional sync between Google Sheets and Infinity CRM
// 
// This is the TEMPLATE SHEET version
// Users will copy this sheet and it will auto-configure
// ============================================================

// ==================== CONFIGURATION ====================

const CONFIG = {
  // Your Supabase Edge Function URL
  WEBHOOK_URL: 'https://whjgmbptnlsxswehlfhq.supabase.co/functions/v1/sheets-webhook',
  
  // Webhook secret (same for all users - identifies the app)
  WEBHOOK_SECRET: 'your-webhook-secret-bffd0b2d86670879037f23b1e1776793d9bea9f22cbe48f32f675095078cbfb4',
  
  // Sync ALL sheets (empty array = sync everything)
  SHEETS_TO_SYNC: [],
  
  // Debounce time in milliseconds (wait for rapid edits to finish)
  DEBOUNCE_MS: 3000,
  
  // Maximum rows per sync batch
  MAX_BATCH_SIZE: 500
};

// ==================== AUTO-SETUP ====================
// Runs once when sheet is first opened (after OAuth callback)

function onOpen() {
  try {
    // ALWAYS ensure trigger is installed (no checks, just do it)
    installTrigger();
    
    // Create menu
    SpreadsheetApp.getUi()
      .createMenu('🔄 Infinity Sync')
      .addItem('📤 Manual Sync', 'manualSync')
      .addItem('📥 Full Sync (All Data)', 'fullSync')
      .addSeparator()
      .addItem('🛑 Disable Auto-Sync', 'disableSync')
      .addSeparator()
      .addItem('ℹ️ Sync Status', 'showStatus')
      .addItem('🧪 Test Connection', 'testConnectionUI')
      .addToUi();
  } catch (error) {
    Logger.log('onOpen error: ' + error.message);
  }
}

function autoSetupSync() {
  try {
    installTrigger();
    testWebhookConnection();
  } catch (error) {
    Logger.log('Auto-setup error: ' + error.message);
  }
}

function installTrigger() {
  try {
    const triggers = ScriptApp.getProjectTriggers();
    
    // Remove any old triggers first
    triggers.forEach(t => {
      if (t.getHandlerFunction() === 'onEditTrigger') {
        ScriptApp.deleteTrigger(t);
      }
    });
    
    // Install fresh trigger
    ScriptApp.newTrigger('onEditTrigger')
      .forSpreadsheet(SpreadsheetApp.getActive())
      .onEdit()
      .create();
    
    Logger.log('✅ Trigger installed successfully');
  } catch (error) {
    Logger.log('Error installing trigger: ' + error.message);
    throw error;
  }
}

// ==================== EDIT TRIGGER ====================
// Called automatically when user edits any cell

function onEditTrigger(e) {
  try {
    const sheet = e.source.getActiveSheet();
    const sheetName = sheet.getName();
    
    // Skip if not a sheet we want to sync
    if (CONFIG.SHEETS_TO_SYNC.length > 0 && !CONFIG.SHEETS_TO_SYNC.includes(sheetName)) {
      return;
    }
    
    // Skip if editing header row (first row)
    if (e.range.getRow() === 1) {
      return;
    }
    
    // Debounce: prevent rapid-fire syncs
    const cache = CacheService.getScriptCache();
    const cacheKey = 'lastEdit_' + sheetName;
    const lastEdit = cache.get(cacheKey);
    const now = Date.now();
    
    if (lastEdit && (now - parseInt(lastEdit)) < CONFIG.DEBOUNCE_MS) {
      return;
    }
    
    cache.put(cacheKey, now.toString(), 300);
    Utilities.sleep(CONFIG.DEBOUNCE_MS);
    
    const currentLastEdit = cache.get(cacheKey);
    if (currentLastEdit && parseInt(currentLastEdit) > now) {
      return;
    }
    
    syncSheet(sheet);
    
  } catch (error) {
    Logger.log('Error in onEditTrigger: ' + error.message);
  }
}

// ==================== SYNC FUNCTIONS ====================

function syncSheet(sheet) {
  const sheetName = sheet.getName();
  const sheetId = SpreadsheetApp.getActive().getId();
  
  Logger.log('Starting sync for sheet: ' + sheetName);
  
  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();
  
  if (values.length < 2) {
    Logger.log('Sheet ' + sheetName + ' has no data rows, skipping');
    return;
  }
  
  const headers = values[0].map(h => h ? h.toString().trim() : '');
  const rows = [];
  
  for (let i = 1; i < Math.min(values.length, CONFIG.MAX_BATCH_SIZE + 1); i++) {
    const row = values[i];
    const hasData = row.some(cell => cell !== '' && cell !== null);
    if (!hasData) continue;
    
    const rowObj = { _rowNumber: i + 1 };
    headers.forEach((header, colIndex) => {
      if (header && header !== '') {
        let value = row[colIndex];
        if (value instanceof Date) {
          value = Utilities.formatDate(value, Session.getScriptTimeZone(), "yyyy-MM-dd");
        }
        rowObj[header] = value;
      }
    });
    rows.push(rowObj);
  }
  
  if (rows.length === 0) return;
  
  const payload = {
    sheetId: sheetId,
    sheetName: sheetName,
    rows: rows,
    timestamp: new Date().toISOString(),
    changeType: 'edit'
  };
  
  const result = sendToWebhook(payload);
  Logger.log('Sync result: ' + JSON.stringify(result));
}

function sendToWebhook(payload) {
  const options = {
    method: 'POST',
    contentType: 'application/json',
    headers: {
      'x-webhook-secret': CONFIG.WEBHOOK_SECRET
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
    timeout: 30
  };
  
  try {
    const response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL, options);
    const responseCode = response.getResponseCode();
    const responseBody = response.getContentText();
    
    if (responseCode === 200) {
      const result = JSON.parse(responseBody);
      Logger.log('Sync successful: ' + result.synced + ' rows');
      return { success: true, synced: result.synced };
    } else {
      Logger.log('Sync failed: ' + responseCode + ' - ' + responseBody);
      return { success: false, error: responseBody };
    }
  } catch (error) {
    Logger.log('Webhook error: ' + error.message);
    return { success: false, error: error.message };
  }
}

// ==================== MANUAL SYNC ====================

function manualSync() {
  const ui = SpreadsheetApp.getUi();
  const confirm = ui.alert('Manual Sync', 'This will sync all data from all sheets.\\n\\nContinue?', ui.ButtonSet.YES_NO);
  if (confirm !== ui.Button.YES) return;
  
  ui.showModelessDialog(HtmlService.createHtmlOutput('<p>Syncing... Please wait.</p>'), 'Sync in Progress');
  
  const sheets = SpreadsheetApp.getActive().getSheets();
  let totalRows = 0;
  let syncedSheets = 0;
  
  sheets.forEach(sheet => {
    const sheetName = sheet.getName();
    if (CONFIG.SHEETS_TO_SYNC.length === 0 || CONFIG.SHEETS_TO_SYNC.includes(sheetName)) {
      syncSheet(sheet);
      totalRows += sheet.getLastRow() - 1;
      syncedSheets++;
    }
  });
  
  ui.alert('✅ Sync Complete', 'Synced ' + syncedSheets + ' sheets (' + totalRows + ' rows total)', ui.ButtonSet.OK);
}

// ==================== FULL SYNC ====================

function fullSync() {
  const ui = SpreadsheetApp.getUi();
  const confirm = ui.alert('⚠️ Full Sync', 'This will sync ALL data from ALL sheets.\\n\\nContinue?', ui.ButtonSet.YES_NO);
  if (confirm !== ui.Button.YES) return;
  
  const sheets = SpreadsheetApp.getActive().getSheets();
  const sheetId = SpreadsheetApp.getActive().getId();
  let totalRows = 0;
  
  sheets.forEach(sheet => {
    const sheetName = sheet.getName();
    if (CONFIG.SHEETS_TO_SYNC.length > 0 && !CONFIG.SHEETS_TO_SYNC.includes(sheetName)) return;
    
    const dataRange = sheet.getDataRange();
    const values = dataRange.getValues();
    if (values.length < 2) return;
    
    const headers = values[0].map(h => h ? h.toString().trim() : '');
    
    for (let batchStart = 1; batchStart < values.length; batchStart += CONFIG.MAX_BATCH_SIZE) {
      const batchEnd = Math.min(batchStart + CONFIG.MAX_BATCH_SIZE, values.length);
      const rows = [];
      
      for (let i = batchStart; i < batchEnd; i++) {
        const row = values[i];
        const hasData = row.some(cell => cell !== '' && cell !== null);
        if (!hasData) continue;
        
        const rowObj = { _rowNumber: i + 1 };
        headers.forEach((header, colIndex) => {
          if (header) {
            let value = row[colIndex];
            if (value instanceof Date) {
              value = Utilities.formatDate(value, Session.getScriptTimeZone(), "yyyy-MM-dd");
            }
            rowObj[header] = value;
          }
        });
        rows.push(rowObj);
      }
      
      if (rows.length > 0) {
        const payload = {
          sheetId: sheetId,
          sheetName: sheetName,
          rows: rows,
          timestamp: new Date().toISOString(),
          changeType: 'full_sync'
        };
        
        sendToWebhook(payload);
        totalRows += rows.length;
        
        if (batchEnd < values.length) {
          Utilities.sleep(1000);
        }
      }
    }
  });
  
  ui.alert('✅ Full Sync Complete', 'Synced ' + totalRows + ' rows total.', ui.ButtonSet.OK);
}

// ==================== UTILITIES ====================

function testWebhookConnection() {
  const testPayload = {
    sheetId: SpreadsheetApp.getActive().getId(),
    sheetName: '_test_connection_',
    rows: [],
    timestamp: new Date().toISOString(),
    changeType: 'test'
  };
  return sendToWebhook(testPayload);
}

function showStatus() {
  const triggers = ScriptApp.getProjectTriggers();
  const hasEditTrigger = triggers.some(t => t.getHandlerFunction() === 'onEditTrigger');
  const sheets = CONFIG.SHEETS_TO_SYNC.length > 0 ? CONFIG.SHEETS_TO_SYNC.join(', ') : 'All sheets';
  
  let status = '';
  status += hasEditTrigger ? '✅ Auto-sync: ENABLED\\n\\n' : '❌ Auto-sync: DISABLED\\n\\n';
  
  if (!hasEditTrigger) {
    status += '⚠️ Trigger not found. Click OK and sheet will auto-enable on refresh.\\n\\n';
  }
  
  status += '📋 Sheets to sync:\\n' + sheets + '\\n\\n';
  status += '🔗 Webhook URL:\\n' + CONFIG.WEBHOOK_URL.substring(0, 50) + '...';
  
  SpreadsheetApp.getUi().alert('Sync Status', status, SpreadsheetApp.getUi().ButtonSet.OK);
}

function disableSync() {
  const triggers = ScriptApp.getProjectTriggers();
  let removed = 0;
  
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'onEditTrigger') {
      ScriptApp.deleteTrigger(trigger);
      removed++;
    }
  });
  
  SpreadsheetApp.getUi().alert('Sync Disabled', 'Removed ' + removed + ' trigger(s).\\n\\nYour sheet will no longer sync automatically.', SpreadsheetApp.getUi().ButtonSet.OK);
}

function testConnectionUI() {
  const result = testWebhookConnection();
  const ui = SpreadsheetApp.getUi();
  
  if (result.success) {
    ui.alert('✅ Connection Test', 'Successfully connected to Infinity!', ui.ButtonSet.OK);
  } else {
    ui.alert('❌ Connection Failed', 'Error: ' + result.error, ui.ButtonSet.OK);
  }
}
`

serve(async (req) => {
    try {
        // Only POST allowed
        if (req.method !== 'POST') {
            return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405 })
        }

        const { sheetId, accessToken } = await req.json()

        if (!sheetId || !accessToken) {
            return new Response(JSON.stringify({ error: 'Missing sheetId or accessToken' }), { status: 400 })
        }

        // Step 1: Get sheet's script ID (or create project if not exists)
        let scriptId: string
        try {
            // Try to get existing script project
            const sheetResponse = await fetch(
                `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}`,
                { headers: { 'Authorization': `Bearer ${accessToken}` } }
            )

            if (!sheetResponse.ok) {
                return new Response(JSON.stringify({ error: 'Could not access sheet', detail: await sheetResponse.text() }), { status: 400 })
            }

            const sheetData = await sheetResponse.json()
            console.log('Sheet data:', JSON.stringify(sheetData))

            // Check if sheet has a linked script (it won't for newly copied sheets)
            // We'll use the Drive API to find or create the bound script

            // Step 2: Get the script project ID from the sheet
            // Google Sheets creates a bound script automatically, we need to find it
            const driveResponse = await fetch(
                `https://www.googleapis.com/drive/v3/files/${sheetId}?fields=appProperties`,
                { headers: { 'Authorization': `Bearer ${accessToken}` } }
            )

            if (!driveResponse.ok) {
                console.error('Drive API error:', await driveResponse.text())
                // If we can't get via Drive, we'll create a new script project
                scriptId = await createBoundScript(sheetId, accessToken)
            } else {
                const driveData = await driveResponse.json()
                scriptId = driveData.appProperties?.scriptId

                if (!scriptId) {
                    // Create new bound script
                    scriptId = await createBoundScript(sheetId, accessToken)
                }
            }
        } catch (error) {
            console.error('Script ID lookup error:', error)
            return new Response(JSON.stringify({ error: 'Failed to get script project', detail: String(error) }), { status: 500 })
        }

        // Step 3: Deploy Code.gs to the script
        try {
            // Get current script files
            const scriptsResponse = await fetch(
                `https://script.googleapis.com/v1/projects/${scriptId}/content`,
                { headers: { 'Authorization': `Bearer ${accessToken}` } }
            )

            if (!scriptsResponse.ok) {
                const errText = await scriptsResponse.text()
                console.error('Scripts API error:', errText)
                return new Response(JSON.stringify({ error: 'Could not access Apps Script project', detail: errText }), { status: 400 })
            }

            const scriptContent = await scriptsResponse.json()

            // Create or update Code.gs file
            const files = scriptContent.files || []
            const codeGsIndex = files.findIndex(f => f.name === 'Code')

            if (codeGsIndex !== -1) {
                // Update existing
                files[codeGsIndex].source = CODE_GS_CONTENT
            } else {
                // Add new
                files.push({
                    name: 'Code',
                    type: 'SERVER_JS',
                    source: CODE_GS_CONTENT
                })
            }

            // Push update to Apps Script
            const updateResponse = await fetch(
                `https://script.googleapis.com/v1/projects/${scriptId}/content`,
                {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ files })
                }
            )

            if (!updateResponse.ok) {
                const errText = await updateResponse.text()
                console.error('Update error:', errText)
                return new Response(JSON.stringify({ error: 'Failed to update script', detail: errText }), { status: 500 })
            }

            console.log('✅ Code.gs deployed successfully to script project:', scriptId)
            return new Response(JSON.stringify({ success: true, scriptId, message: 'Code.gs deployed! Refresh your sheet to see the Infinity Sync menu.' }), { status: 200 })

        } catch (error) {
            console.error('Deployment error:', error)
            return new Response(JSON.stringify({ error: 'Failed to deploy code', detail: String(error) }), { status: 500 })
        }

    } catch (error) {
        console.error('Unexpected error:', error)
        return new Response(JSON.stringify({ error: 'Internal server error', detail: String(error) }), { status: 500 })
    }
})

// Helper function to create a bound script project
async function createBoundScript(sheetId: string, accessToken: string): Promise<string> {
    // Google Apps Script API requires creating a project first
    // This is complex, so we'll use an alternative: create via Drive API

    const createResponse = await fetch(
        'https://script.googleapis.com/v1/projects',
        {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: 'Infinity Sync Script',
                parentId: sheetId  // Bind to the sheet
            })
        }
    )

    if (!createResponse.ok) {
        throw new Error(`Failed to create script project: ${await createResponse.text()}`)
    }

    const result = await createResponse.json()
    return result.scriptId
}
