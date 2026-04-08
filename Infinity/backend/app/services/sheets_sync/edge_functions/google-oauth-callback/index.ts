// ============================================================
// EDGE FUNCTION: google-oauth-callback
// Handles OAuth callback, stores tokens, and AUTO-CREATES SHEET
// One-click experience: Authorize → Sheet Created → Success!
// ============================================================

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')

serve(async (req) => {
    try {
        const url = new URL(req.url)
        const code = url.searchParams.get('code')
        const state = url.searchParams.get('state')
        const error = url.searchParams.get('error')

        // Handle OAuth errors
        if (error) {
            return errorPage('Authorization Failed', error)
        }

        if (!code || !state) {
            return errorPage('Invalid Request', 'Missing code or state parameter')
        }

        // Decode state to get userId
        let userId: string
        try {
            const stateData = JSON.parse(atob(state))
            userId = stateData.userId
        } catch {
            return errorPage('Invalid State', 'Could not decode state parameter')
        }

        // Initialize Supabase
        const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
        const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
        
        const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey)

        // Get OAuth credentials
        let clientId = Deno.env.get('GOOGLE_CLIENT_ID')
        const clientSecret = Deno.env.get('GOOGLE_CLIENT_SECRET')!
        const redirectUri = `${supabaseUrl}/functions/v1/google-oauth-callback`

        // If not in env, fetch from database
        if (!clientId) {
            const { data: idConfig, error: idError } = await supabaseAdmin
                .from('app_config')
                .select('value')
                .eq('key', 'google_client_id')
                .single()

            if (idError || !idConfig?.value) {
                return errorPage('Configuration Error', `google_client_id not found: ${idError?.message || 'missing'}`)
            }
            clientId = idConfig.value
            console.log('Loaded google_client_id from database')
        }

        // Exchange code for tokens
        const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                code,
                client_id: clientId,
                client_secret: clientSecret,
                redirect_uri: redirectUri,
                grant_type: 'authorization_code',
            }),
        })

        if (!tokenResponse.ok) {
            const err = await tokenResponse.text()
            console.error('Token exchange failed:', err)
            return errorPage('Token Exchange Failed', err)
        }

        const tokens = await tokenResponse.json()
        const accessToken = tokens.access_token

        // Get user's email from Google
        const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        })

        let email = ''
        if (userInfoResponse.ok) {
            const userInfo = await userInfoResponse.json()
            email = userInfo.email
        }

        // Calculate token expiry
        const expiresAt = new Date(Date.now() + (tokens.expires_in * 1000))

        // Check if user exists, if not create basic profile
        const { data: existingProfile, error: checkError } = await supabaseAdmin
            .from('mfd_profiles')
            .select('user_id')
            .eq('user_id', userId)
            .single()

        console.log('User check:', existingProfile ? 'exists' : 'new', 'Error:', checkError?.message)

        if (!existingProfile && checkError?.code === 'PGRST116') {
            // User doesn't exist, create new profile
            console.log('Creating new profile for user:', userId)
            const { error: createError } = await supabaseAdmin
                .from('mfd_profiles')
                .insert({
                    user_id: userId,
                    google_connected: true,
                    google_email: email,
                    google_access_token: tokens.access_token,
                    google_refresh_token: tokens.refresh_token,
                    google_token_expiry: expiresAt.toISOString(),
                })
            
            if (createError) {
                console.error('Create profile error:', createError)
                return errorPage('Database Error', `Failed to create profile: ${createError.message}`)
            }
        } else {
            // User exists, update profile
            console.log('Updating existing profile for user:', userId)
            const { error: updateError } = await supabaseAdmin
                .from('mfd_profiles')
                .update({
                    google_connected: true,
                    google_email: email,
                    google_access_token: tokens.access_token,
                    google_refresh_token: tokens.refresh_token,
                    google_token_expiry: expiresAt.toISOString(),
                    updated_at: new Date().toISOString(),
                })
                .eq('user_id', userId)

            if (updateError) {
                console.error('Update profile error:', updateError)
                return errorPage('Database Error', `Failed to update profile: ${updateError.message}`)
            }
        }

        // ==================== AUTO-CREATE SHEET ====================

        try {
            // Get user profile to check for existing sheet
            const { data: profile } = await supabaseAdmin
                .from('mfd_profiles')
                .select('*')
                .eq('user_id', userId)
                .single()

            console.log('Checking for existing sheet... google_sheet_id:', profile?.google_sheet_id)

            if (profile?.google_sheet_id) {
                // User already has a sheet - NO NEED TO CREATE AGAIN
                console.log('User already has sheet:', profile.google_sheet_id, '- Skipping creation')
                const sheetUrl = `https://docs.google.com/spreadsheets/d/${profile.google_sheet_id}/edit`
                const clientsUrl = profile.google_clients_folder_id ? `https://drive.google.com/drive/folders/${profile.google_clients_folder_id}` : null
                return successPage(email, sheetUrl, clientsUrl, '✅ Your sheet is ready! (Already created)')
            }

            // Get template sheet ID
            const { data: configData } = await supabaseAdmin
                .from('app_config')
                .select('value')
                .eq('key', 'template_sheet_id')
                .single()

            if (!configData?.value) {
                return errorPage('Configuration Error', 'Template sheet not configured')
            }

            const templateSheetId = configData.value
            const userName = email.split('@')[0]

            // Create folders
            console.log('Creating folder structure...')
            const mySheetsFolder = await createFolder(accessToken, `${userName} - My Sheets`, null)
            const clientsFolder = await createFolder(accessToken, `${userName} - Clients`, null)

        // Create A-Z subfolders
        const letterFolders: Record<string, string> = {}
        for (const letter of ALPHABET) {
            const folder = await createFolder(accessToken, letter, clientsFolder.id)
            letterFolders[letter] = folder.id
        }

        // Copy template sheet
        console.log('Copying template sheet...')
        const newSheetTitle = `${userName} - Infinity Sheet`
        const copyResponse = await fetch(
            `https://www.googleapis.com/drive/v3/files/${templateSheetId}/copy`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: newSheetTitle,
                    parents: [mySheetsFolder.id],
                }),
            }
        )

        if (!copyResponse.ok) {
            const err = await copyResponse.text()
            console.error('Copy error:', err)
            return errorPage('Sheet Creation Failed', err)
        }

        const copyResult = await copyResponse.json()
        const newSheetId = copyResult.id
        const sheetUrl = `https://docs.google.com/spreadsheets/d/${newSheetId}/edit`
        const clientsUrl = `https://drive.google.com/drive/folders/${clientsFolder.id}`

        // Store folder and sheet info in mfd_profiles
        await supabaseAdmin
            .from('mfd_profiles')
            .update({
                google_drive_folder_id: mySheetsFolder.id,
                google_sheet_id: newSheetId,
                google_clients_folder_id: clientsFolder.id,
                updated_at: new Date().toISOString(),
            })
            .eq('user_id', userId)

        // ==================== AUTO-DEPLOY APPSCRIPT CODE ====================
        console.log('Deploying AppScript code to new sheet...')
        
        try {
            // Get service account from config
            const { data: saConfig } = await supabaseAdmin
                .from('app_config')
                .select('value')
                .eq('key', 'google_service_account')
                .single()

            if (saConfig?.value) {
                const serviceAccount = JSON.parse(saConfig.value)
                await deployScriptToSheet(newSheetId, serviceAccount)
                console.log('✅ AppScript code deployed successfully')
            } else {
                console.error('Service account config not found - script deployment skipped')
            }
        } catch (deployErr) {
            console.error('Script deployment failed (non-fatal):', deployErr)
            // Continue anyway - user can still use sheet
        }

        // Log success
        console.log('Setup complete for user:', email)

        return successPage(email, sheetUrl, clientsUrl, 'Your workspace is ready! Auto-sync is enabled.')
        
        } catch (sheetErr) {
            console.error('Sheet creation error:', sheetErr)
            return errorPage('Sheet Creation Failed', (sheetErr as Error).message)
        }

    } catch (err) {
        console.error('Callback error:', err)
        return errorPage('Error', (err as Error).message)
    }
})

// ==================== HELPER: Create Folder ====================
async function createFolder(accessToken: string, name: string, parentId: string | null) {
    const metadata: Record<string, unknown> = {
        name,
        mimeType: 'application/vnd.google-apps.folder',
    }
    if (parentId) metadata.parents = [parentId]

    const response = await fetch('https://www.googleapis.com/drive/v3/files', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(metadata),
    })

    if (!response.ok) {
        throw new Error(`Failed to create folder "${name}"`)
    }
    return response.json()
}

// ==================== SUCCESS PAGE ====================
function successPage(email: string, sheetUrl: string, clientsUrl: string | null, message: string) {
    return new Response(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Setup Complete!</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }
        .card {
            background: white;
            border-radius: 24px;
            padding: 48px;
            max-width: 480px;
            width: 100%;
            box-shadow: 0 25px 50px rgba(0,0,0,0.25);
            text-align: center;
        }
        .icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 24px;
            font-size: 40px;
        }
        h1 {
            color: #1f2937;
            font-size: 28px;
            margin-bottom: 8px;
        }
        .subtitle {
            color: #6b7280;
            font-size: 16px;
            margin-bottom: 24px;
        }
        .email {
            background: #f3f4f6;
            padding: 12px 20px;
            border-radius: 12px;
            margin-bottom: 32px;
            font-weight: 600;
            color: #374151;
        }
        .buttons {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 16px 24px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }
        .btn-primary {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
        }
        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
        }
        .footer {
            margin-top: 32px;
            color: #9ca3af;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">✓</div>
        <h1>${message}</h1>
        <p class="subtitle">Connected as:</p>
        <div class="email">${email}</div>
        
        <div class="buttons">
            <a href="${sheetUrl}" class="btn btn-primary" target="_blank">
                📊 Open Your Sheet
            </a>
            ${clientsUrl ? `<a href="${clientsUrl}" class="btn btn-secondary" target="_blank">
                📁 Open Clients Folder
            </a>` : ''}
        </div>
        
        <p class="footer">You can close this window</p>
    </div>
</body>
</html>
    `, { headers: { 'Content-Type': 'text/html; charset=utf-8' } })
}

// ==================== ERROR PAGE ====================
function errorPage(title: string, message: string) {
    return new Response(`
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Error</title>
    <style>
        body {
            font-family: -apple-system, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #ef4444, #dc2626);
            padding: 20px;
        }
        .card {
            background: white;
            border-radius: 24px;
            padding: 48px;
            max-width: 480px;
            text-align: center;
            box-shadow: 0 25px 50px rgba(0,0,0,0.25);
        }
        h1 { color: #ef4444; margin-bottom: 16px; }
        p { color: #6b7280; word-break: break-word; }
    </style>
</head>
<body>
    <div class="card">
        <h1>❌ ${title}</h1>
        <p>${message}</p>
    </div>
</body>
</html>
    `, { headers: { 'Content-Type': 'text/html; charset=utf-8' } })
}

// ==================== AUTO-DEPLOY APPSCRIPT ====================

const APPSCRIPT_CODE = `
// INFINITY SYNC - Auto-deployed AppScript
const CONFIG = {
  WEBHOOK_URL: 'https://whjgmbptnlsxswehlfhq.supabase.co/functions/v1/sheets-webhook',
  WEBHOOK_SECRET: 'your-webhook-secret-bffd0b2d86670879037f23b1e1776793d9bea9f22cbe48f32f675095078cbfb4',
  SHEETS_TO_SYNC: [],
  DEBOUNCE_MS: 3000,
  MAX_BATCH_SIZE: 500
};

function onOpen() {
  try {
    installTrigger();
    SpreadsheetApp.getUi().createMenu('🔄 Infinity Sync')
      .addItem('📤 Manual Sync', 'manualSync')
      .addItem('📥 Full Sync', 'fullSync')
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

function installTrigger() {
  try {
    const triggers = ScriptApp.getProjectTriggers();
    triggers.forEach(t => {
      if (t.getHandlerFunction() === 'onEditTrigger') {
        ScriptApp.deleteTrigger(t);
      }
    });
    ScriptApp.newTrigger('onEditTrigger').forSpreadsheet(SpreadsheetApp.getActive()).onEdit().create();
    Logger.log('✅ Trigger installed');
  } catch (error) {
    Logger.log('Error: ' + error.message);
  }
}

function onEditTrigger(e) {
  try {
    const sheet = e.source.getActiveSheet();
    const sheetName = sheet.getName();
    if (CONFIG.SHEETS_TO_SYNC.length > 0 && !CONFIG.SHEETS_TO_SYNC.includes(sheetName)) return;
    if (e.range.getRow() === 1) return;
    const cache = CacheService.getScriptCache();
    const cacheKey = 'lastEdit_' + sheetName;
    const lastEdit = cache.get(cacheKey);
    const now = Date.now();
    if (lastEdit && (now - parseInt(lastEdit)) < CONFIG.DEBOUNCE_MS) return;
    cache.put(cacheKey, now.toString(), 300);
    Utilities.sleep(CONFIG.DEBOUNCE_MS);
    syncSheet(sheet);
  } catch (error) {
    Logger.log('Error: ' + error.message);
  }
}

function syncSheet(sheet) {
  const sheetName = sheet.getName();
  const sheetId = SpreadsheetApp.getActive().getId();
  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();
  if (values.length < 2) return;
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
          value = Utilities.formatDate(value, Session.getScriptTimeZone(), 'yyyy-MM-dd');
        }
        rowObj[header] = value;
      }
    });
    rows.push(rowObj);
  }
  if (rows.length === 0) return;
  const payload = { sheetId: sheetId, sheetName: sheetName, rows: rows, timestamp: new Date().toISOString(), changeType: 'edit' };
  sendToWebhook(payload);
}

function sendToWebhook(payload) {
  const options = {
    method: 'POST',
    contentType: 'application/json',
    headers: { 'x-webhook-secret': CONFIG.WEBHOOK_SECRET },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
    timeout: 30
  };
  try {
    const response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL, options);
    const responseCode = response.getResponseCode();
    if (responseCode === 200) {
      const result = JSON.parse(response.getContentText());
      Logger.log('Sync successful: ' + result.synced + ' rows');
      return { success: true, synced: result.synced };
    }
  } catch (error) {
    Logger.log('Webhook error: ' + error.message);
  }
  return { success: false };
}

function manualSync() {
  const ui = SpreadsheetApp.getUi();
  if (ui.alert('Manual Sync', 'Sync all data?', ui.ButtonSet.YES_NO) !== ui.Button.YES) return;
  const sheets = SpreadsheetApp.getActive().getSheets();
  sheets.forEach(sheet => {
    if (CONFIG.SHEETS_TO_SYNC.length === 0) syncSheet(sheet);
  });
  ui.alert('✅ Done', 'Sync complete', ui.ButtonSet.OK);
}

function fullSync() {
  const ui = SpreadsheetApp.getUi();
  if (ui.alert('Full Sync', 'Sync ALL data?', ui.ButtonSet.YES_NO) !== ui.Button.YES) return;
  const sheets = SpreadsheetApp.getActive().getSheets();
  sheets.forEach(syncSheet);
  ui.alert('✅ Done', 'Full sync complete', ui.ButtonSet.OK);
}

function testWebhookConnection() {
  return sendToWebhook({ sheetId: SpreadsheetApp.getActive().getId(), sheetName: '_test_', rows: [], timestamp: new Date().toISOString(), changeType: 'test' });
}

function showStatus() {
  const triggers = ScriptApp.getProjectTriggers();
  const hasEditTrigger = triggers.some(t => t.getHandlerFunction() === 'onEditTrigger');
  SpreadsheetApp.getUi().alert('Sync Status', hasEditTrigger ? '✅ Auto-sync: ENABLED' : '❌ Auto-sync: DISABLED', SpreadsheetApp.getUi().ButtonSet.OK);
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
  SpreadsheetApp.getUi().alert('Sync Disabled', 'Removed ' + removed + ' trigger(s)', SpreadsheetApp.getUi().ButtonSet.OK);
}

function testConnectionUI() {
  const result = testWebhookConnection();
  const ui = SpreadsheetApp.getUi();
  if (result.success) {
    ui.alert('✅ Connection Test', 'Connected!', ui.ButtonSet.OK);
  } else {
    ui.alert('❌ Connection Failed', 'Error', ui.ButtonSet.OK);
  }
}
`

async function deployScriptToSheet(sheetId: string, serviceAccount: Record<string, unknown>) {
    try {
        const saEmail = serviceAccount.client_email as string
        const saPrivateKey = serviceAccount.private_key as string
        const accessToken = await getServiceAccountToken(saEmail, saPrivateKey)
        
        const createResponse = await fetch('https://script.googleapis.com/v1/projects', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: 'Infinity Sync', parentId: sheetId }),
        })

        if (!createResponse.ok) {
            console.error('Failed to create script project:', await createResponse.text())
            return
        }

        const project = await createResponse.json()
        const projectId = project.scriptId

        const filesResponse = await fetch(
            `https://script.googleapis.com/v1/projects/${projectId}/content`,
            {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    files: [{ name: 'Code', type: 'SERVER_JS', source: APPSCRIPT_CODE }],
                }),
            }
        )

        if (!filesResponse.ok) {
            console.error('Failed to create script file:', await filesResponse.text())
            return
        }

        console.log('✅ AppScript deployed')
    } catch (error) {
        console.error('Deploy error:', error)
    }
}

async function getServiceAccountToken(email: string, privateKey: string): Promise<string> {
    const now = Math.floor(Date.now() / 1000)
    const header = { alg: 'RS256', typ: 'JWT' }
    const payload = {
        iss: email,
        scope: 'https://www.googleapis.com/auth/script.projects',
        aud: 'https://oauth2.googleapis.com/token',
        exp: now + 3600,
        iat: now,
    }

    const headerEncoded = btoa(JSON.stringify(header))
    const payloadEncoded = btoa(JSON.stringify(payload))
    const signatureInput = `${headerEncoded}.${payloadEncoded}`
    const signature = await signJwt(signatureInput, privateKey)
    const jwt = `${signatureInput}.${signature}`

    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
            grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            assertion: jwt,
        }),
    })

    const tokenData = await tokenResponse.json()
    return tokenData.access_token
}

async function signJwt(input: string, privateKey: string): Promise<string> {
    const keyData = privateKey
        .replace(/-----BEGIN PRIVATE KEY-----/g, '')
        .replace(/-----END PRIVATE KEY-----/g, '')
        .replace(/\n/g, '')
    
    const binaryKey = Uint8Array.from(atob(keyData), c => c.charCodeAt(0))
    
    const key = await crypto.subtle.importKey(
        'pkcs8',
        binaryKey,
        { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
        false,
        ['sign']
    )
    
    const signature = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(input))
    return btoa(String.fromCharCode(...new Uint8Array(signature)))
}
