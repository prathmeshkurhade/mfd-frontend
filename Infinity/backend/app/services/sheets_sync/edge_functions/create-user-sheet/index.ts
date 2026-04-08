// ============================================================
// EDGE FUNCTION: create-user-sheet
// Creates folder structure and sheet in USER'S OWN Google Drive
// Uses user's OAuth token (not service account)
// ============================================================

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

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
        const { data: existingSheet } = await supabaseAdmin
            .from('user_sheets')
            .select('*')
            .eq('user_id', userId)
            .eq('is_active', true)
            .single()

        if (existingSheet) {
            return new Response(
                JSON.stringify({
                    error: 'User already has an active sheet',
                    existingSheet: {
                        sheetId: existingSheet.sheet_id,
                        sheetUrl: existingSheet.sheet_url,
                        sheetName: existingSheet.sheet_name
                    }
                }),
                { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        // ==================== GET USER'S OAUTH TOKEN ====================
        const { data: tokenData, error: tokenError } = await supabaseAdmin
            .from('user_oauth_tokens')
            .select('*')
            .eq('user_id', userId)
            .eq('provider', 'google')
            .single()

        if (!tokenData || tokenError) {
            return new Response(
                JSON.stringify({
                    error: 'Google Drive not connected. Please connect your Google account first.',
                    action: 'connect_google'
                }),
                { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        // Check if token needs refresh
        let accessToken = tokenData.access_token
        const tokenExpiresAt = new Date(tokenData.token_expires_at)

        if (tokenExpiresAt <= new Date()) {
            console.log('Token expired, refreshing...')
            accessToken = await refreshAccessToken(tokenData.refresh_token, supabaseAdmin, userId)
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

        // ==================== REGISTER IN DATABASE ====================
        const sheetUrl = `https://docs.google.com/spreadsheets/d/${newSheetId}/edit`
        const mySheetsUrl = `https://drive.google.com/drive/folders/${mySheetsFolder.id}`
        const clientsUrl = `https://drive.google.com/drive/folders/${clientsFolder.id}`

        const { error: insertError } = await supabaseAdmin
            .from('user_sheets')
            .insert({
                user_id: userId,
                sheet_id: newSheetId,
                sheet_url: sheetUrl,
                sheet_name: newSheetTitle,
                is_active: true,
            })

        if (insertError) {
            console.error('DB insert error:', insertError)
        }

        // Store folder IDs for future reference
        await supabaseAdmin
            .from('user_oauth_tokens')
            .update({
                metadata: {
                    ...tokenData.metadata,
                    folders: {
                        mySheetsFolderId: mySheetsFolder.id,
                        clientsFolderId: clientsFolder.id,
                        letterFolders: letterFolders
                    }
                }
            })
            .eq('user_id', userId)
            .eq('provider', 'google')

        // ==================== LOG SUCCESS ====================
        await supabaseAdmin.from('sync_log').insert({
            user_id: userId,
            sheet_id: newSheetId,
            operation: 'create_sheet_with_folders',
            direction: 'db_to_sheets',
            rows_affected: 0,
            status: 'success',
            metadata: {
                userEmail,
                sheetName: newSheetTitle,
                mySheetsFolderId: mySheetsFolder.id,
                clientsFolderId: clientsFolder.id,
                letterFolders: letterFolders,
                createdInUserDrive: true
            }
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

    // Update token in database
    const expiresAt = new Date(Date.now() + data.expires_in * 1000).toISOString()

    await supabaseAdmin
        .from('user_oauth_tokens')
        .update({
            access_token: data.access_token,
            token_expires_at: expiresAt,
        })
        .eq('user_id', userId)
        .eq('provider', 'google')

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
