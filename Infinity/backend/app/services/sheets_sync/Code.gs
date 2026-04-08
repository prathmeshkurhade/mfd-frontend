// ============================================================
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
// Runs once when sheet is first opened

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🔄 Infinity Sync')
    .addItem('📤 Manual Sync', 'manualSync')
    .addItem('📥 Full Sync (All Data)', 'fullSync')
    .addSeparator()
    .addItem('⚙️ Enable Auto-Sync', 'setupTrigger')
    .addItem('🛑 Disable Auto-Sync', 'disableSync')
    .addSeparator()
    .addItem('ℹ️ Sync Status', 'showStatus')
    .addItem('🧪 Test Connection', 'testConnectionUI')
    .addToUi();
}

// ==================== SETUP TRIGGER ====================
// User clicks "Enable Auto-Sync" to run this

function setupTrigger() {
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
    
    // Test connection
    const testResult = testWebhookConnection();
    
    const ui = SpreadsheetApp.getUi();
    if (testResult.success) {
      ui.alert('✅ Auto-Sync Enabled!', 'Your sheet is connected to Infinity.\n\nChanges will sync automatically.', ui.ButtonSet.OK);
    } else {
      ui.alert('⚠️ Trigger installed (warning)', 'Webhook test failed:\n\n' + testResult.error + '\n\nCheck your CONFIG settings.', ui.ButtonSet.OK);
    }
    
    Logger.log('✅ Trigger installed successfully');
  } catch (error) {
    Logger.log('Error installing trigger: ' + error.message);
    SpreadsheetApp.getUi().alert('❌ Error', 'Failed to enable auto-sync: ' + error.message, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

function autoSetupSync() {
  try {
    setupTrigger();
  } catch (error) {
    Logger.log('Auto-setup error: ' + error.message);
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
  
  // For Client Profile, headers are on row 3, data starts from row 4
  // For others, headers are on row 1, data starts from row 2
  let headerRowIndex = 0;
  let dataStartRowIndex = 1;
  
  if (sheetName === 'Client Profile') {
    headerRowIndex = 2;  // row 3 (0-indexed)
    dataStartRowIndex = 3;  // row 4 (0-indexed)
  }
  
  if (values.length <= headerRowIndex) {
    Logger.log('Sheet ' + sheetName + ' has no headers, skipping');
    return;
  }
  
  const headers = values[headerRowIndex].map(h => h ? h.toString().trim() : '');
  const rows = [];
  
  for (let i = dataStartRowIndex; i < Math.min(values.length, dataStartRowIndex + CONFIG.MAX_BATCH_SIZE); i++) {
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
  const confirm = ui.alert('Manual Sync', 'This will sync all data from all sheets.\n\nContinue?', ui.ButtonSet.YES_NO);
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
  const confirm = ui.alert('⚠️ Full Sync', 'This will sync ALL data from ALL sheets.\n\nContinue?', ui.ButtonSet.YES_NO);
  if (confirm !== ui.Button.YES) return;
  
  const sheets = SpreadsheetApp.getActive().getSheets();
  const sheetId = SpreadsheetApp.getActive().getId();
  let totalRows = 0;
  
  sheets.forEach(sheet => {
    const sheetName = sheet.getName();
    if (CONFIG.SHEETS_TO_SYNC.length > 0 && !CONFIG.SHEETS_TO_SYNC.includes(sheetName)) return;
    
    const dataRange = sheet.getDataRange();
    const values = dataRange.getValues();
    
    // For Client Profile, headers are on row 3, data starts from row 4
    // For others, headers are on row 1, data starts from row 2
    let headerRowIndex = 0;
    let dataStartRowIndex = 1;
    
    if (sheetName === 'Client Profile') {
      headerRowIndex = 2;  // row 3 (0-indexed)
      dataStartRowIndex = 3;  // row 4 (0-indexed)
    }
    
    if (values.length <= headerRowIndex) return;
    
    const headers = values[headerRowIndex].map(h => h ? h.toString().trim() : '');
    
    for (let batchStart = dataStartRowIndex; batchStart < values.length; batchStart += CONFIG.MAX_BATCH_SIZE) {
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
  status += hasEditTrigger ? '✅ Auto-sync: ENABLED\n\n' : '❌ Auto-sync: DISABLED\n\n';
  
  if (!hasEditTrigger) {
    status += '⚠️ Trigger not found. Click OK and sheet will auto-enable on refresh.\n\n';
  }
  
  status += '📋 Sheets to sync:\n' + sheets + '\n\n';
  status += '🔗 Webhook URL:\n' + CONFIG.WEBHOOK_URL.substring(0, 50) + '...';
  
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
  
  SpreadsheetApp.getUi().alert('Sync Disabled', 'Removed ' + removed + ' trigger(s).\n\nYour sheet will no longer sync automatically.', SpreadsheetApp.getUi().ButtonSet.OK);
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