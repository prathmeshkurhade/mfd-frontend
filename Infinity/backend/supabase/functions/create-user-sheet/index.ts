// ============================================================
// EDGE FUNCTION: create-user-sheet  (v3.0 — Production Ready)
// Creates folder structure and sheet in USER'S OWN Google Drive
// Uses user's OAuth token (not service account)
//
// UPGRADES APPLIED:
//   1. Service account auto-sharing (already present)
//   2. Set sync_needed = true on mfd_profiles (NEW)
//      so the first cron cycle picks up the new user
// ============================================================

// @ts-ignore: Deno imports work in Supabase Edge Functions runtime
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
// @ts-ignore: Deno imports work in Supabase Edge Functions runtime
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// Deno global is available in Supabase Edge Functions runtime
declare const Deno: any

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface CreateSheetRequest {
    sheetName?: string
}

const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')

serve(async (req) => {
    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        // ==================== AUTH CHECK ====================
        const authHeader = req.headers.get('Authorization')
        if (!authHeader) {
            return new Response(
                JSON.stringify({ error: 'Missing authorization header' }),
                { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        // Initialize Supabase clients
        const supabaseAdmin = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
        )

        const supabaseUser = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_ANON_KEY') ?? '',
            { global: { headers: { Authorization: authHeader } } }
        )

        // Get current user from JWT
        const { data: { user }, error: userError } = await supabaseUser.auth.getUser()

        if (!user || userError) {
            return new Response(
                JSON.stringify({ error: 'Unauthorized. Valid JWT required.' }),
                { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        const userId = user.id
        const userEmail = user.email ?? ''

        // ==================== PARSE REQUEST ====================
        const body = await req.json().catch(() => ({}))
        const { sheetName } = body as CreateSheetRequest

        // ==================== CHECK IF USER ALREADY HAS SHEET ====================
        const { data: profile } = await supabaseAdmin
            .from('mfd_profiles')
            .select('*')
            .eq('user_id', userId)
            .single()

        if (!profile) {
            return new Response(
                JSON.stringify({ error: 'User profile not found' }),
                { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        if (profile.google_sheet_id) {
            return new Response(
                JSON.stringify({
                    error: 'User already has an active sheet',
                    existingSheet: {
                        sheetId: profile.google_sheet_id,
                        sheetUrl: `https://docs.google.com/spreadsheets/d/${profile.google_sheet_id}/edit`,
                        sheetName: `${profile.name || 'My'} - Infinity Sheet`
                    }
                }),
                { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        // ==================== GET USER'S OAUTH TOKEN FROM PROFILE ====================
        if (!profile.google_connected || !profile.google_access_token) {
            return new Response(
                JSON.stringify({
                    error: 'Google Drive not connected. Please connect your Google account first.',
                    action: 'connect_google'
                }),
                { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        let accessToken = profile.google_access_token
        const tokenExpiresAt = new Date(profile.google_token_expiry || 0)

        if (tokenExpiresAt <= new Date()) {
            console.log('Token expired, refreshing...')
            accessToken = await refreshAccessToken(profile.google_refresh_token, supabaseAdmin, userId)
        }

        // ==================== GET TEMPLATE SHEET ID ====================
        const { data: configData } = await supabaseAdmin
            .from('app_config')
            .select('value')
            .eq('key', 'template_sheet_id')
            .single()

        if (!configData?.value) {
            return new Response(
                JSON.stringify({ error: 'Template sheet not configured. Set template_sheet_id in app_config' }),
                { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        const templateSheetId = configData.value

        // ==================== CREATE FOLDER STRUCTURE ====================
        const userName = userEmail.split('@')[0]

        // 1. Create "My Sheets" folder in user's Drive
        console.log('Creating "My Sheets" folder...')
        const mySheetsFolder = await createFolder(accessToken, `${userName} - My Sheets`, null)

        // 2. Create "Clients" folder in user's Drive
        console.log('Creating "Clients" folder...')
        const clientsFolder = await createFolder(accessToken, `${userName} - Clients`, null)

        // 3. Create A-Z subfolders inside Clients
        console.log('Creating A-Z subfolders...')
        const letterFolders: Record<string, string> = {}
        for (const letter of ALPHABET) {
            const folder = await createFolder(accessToken, letter, clientsFolder.id)
            letterFolders[letter] = folder.id
        }

        // ==================== COPY TEMPLATE SHEET TO USER'S DRIVE ====================
        const newSheetTitle = sheetName || `${userName} - Infinity Sheet`

        console.log('Copying template sheet to user\'s Drive...')
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
            const error = await copyResponse.text()
            console.error('Copy error:', error)
            throw new Error(`Failed to copy template: ${error}`)
        }

        const copyResult = await copyResponse.json()
        const newSheetId = copyResult.id

        console.log(`Created sheet in user's Drive: ${newSheetId}`)

        // ==================== SHARE SHEET WITH SERVICE ACCOUNT ====================
        // The service account needs editor access to read/write during sync
        const { data: saConfigData } = await supabaseAdmin
            .from('app_config')
            .select('value')
            .eq('key', 'google_service_account')
            .single()

        if (saConfigData?.value) {
            const serviceAccount = JSON.parse(saConfigData.value)
            const serviceAccountEmail = serviceAccount.client_email

            console.log(`Sharing sheet with service account: ${serviceAccountEmail}`)

            const shareResponse = await fetch(
                `https://www.googleapis.com/drive/v3/files/${newSheetId}/permissions`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,  // user's OAuth token
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        type: 'user',
                        role: 'writer',
                        emailAddress: serviceAccountEmail,
                        sendNotificationEmail: false,
                    }),
                }
            )

            if (!shareResponse.ok) {
                const shareError = await shareResponse.text()
                console.error('Failed to share sheet with service account:', shareError)
                // Don't throw — sheet creation still succeeded, sync just won't work until this is fixed
            } else {
                console.log('Sheet shared with service account successfully')
            }
        } else {
            console.warn('No service account configured in app_config - sheet sync will not work')
        }

        // ==================== UPDATE MFD_PROFILES WITH ALL IDS ====================
        const sheetUrl = `https://docs.google.com/spreadsheets/d/${newSheetId}/edit`
        const mySheetsUrl = `https://drive.google.com/drive/folders/${mySheetsFolder.id}`
        const clientsUrl = `https://drive.google.com/drive/folders/${clientsFolder.id}`

        const { error: profileUpdateError } = await supabaseAdmin
            .from('mfd_profiles')
            .update({ 
                google_sheet_id: newSheetId,
                google_drive_folder_id: mySheetsFolder.id,
                google_clients_folder_id: clientsFolder.id,
                sync_needed: true 
            })
            .eq('user_id', userId)

        if (profileUpdateError) {
            console.error('Failed to update mfd_profiles:', profileUpdateError)
        } else {
            console.log(`mfd_profiles updated: google_sheet_id=${newSheetId}, sync_needed=true`)
        }

        // ==================== LOG SUCCESS ====================
        await supabaseAdmin.from('excel_sync_logs').insert({
            user_id: userId,
            sync_type: 'create_sheet',
            sync_direction: 'app_to_excel',
            records_synced: 0,
            status: 'success',
            started_at: new Date().toISOString(),
            completed_at: new Date().toISOString()
        })

        return new Response(
            JSON.stringify({
                success: true,
                sheetId: newSheetId,
                sheetUrl: sheetUrl,
                sheetName: newSheetTitle,
                folders: {
                    mySheets: {
                        id: mySheetsFolder.id,
                        url: mySheetsUrl,
                    },
                    clients: {
                        id: clientsFolder.id,
                        url: clientsUrl,
                        letterFolders: letterFolders,
                    },
                },
                message: `Sheet and folders created in your Google Drive`
            }),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )

    } catch (error) {
        console.error('Error:', error)
        return new Response(
            JSON.stringify({ error: error.message }),
            { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
    }
})

// ==================== HELPER: Refresh Access Token ====================
async function refreshAccessToken(
    refreshToken: string,
    supabaseAdmin: any,
    userId: string
): Promise<string> {
    const clientId = Deno.env.get('GOOGLE_CLIENT_ID')!
    const clientSecret = Deno.env.get('GOOGLE_CLIENT_SECRET')!

    const response = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            client_id: clientId,
            client_secret: clientSecret,
            refresh_token: refreshToken,
            grant_type: 'refresh_token',
        }),
    })

    if (!response.ok) {
        const error = await response.text()
        throw new Error(`Failed to refresh token: ${error}`)
    }

    const data = await response.json()

    // Update token in mfd_profiles
    const expiresAt = new Date(Date.now() + data.expires_in * 1000).toISOString()

    await supabaseAdmin
        .from('mfd_profiles')
        .update({
            google_access_token: data.access_token,
            google_token_expiry: expiresAt,
        })
        .eq('user_id', userId)

    return data.access_token
}

// ==================== HELPER: Create Google Drive Folder ====================
async function createFolder(
    accessToken: string,
    name: string,
    parentId: string | null
): Promise<{ id: string; name: string }> {
    const metadata: any = {
        name: name,
        mimeType: 'application/vnd.google-apps.folder',
    }

    if (parentId) {
        metadata.parents = [parentId]
    }

    const response = await fetch('https://www.googleapis.com/drive/v3/files', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(metadata),
    })

    if (!response.ok) {
        const error = await response.text()
        throw new Error(`Failed to create folder "${name}": ${error}`)
    }

    return await response.json()
}