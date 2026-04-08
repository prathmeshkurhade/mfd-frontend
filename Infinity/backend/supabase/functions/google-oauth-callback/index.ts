// ============================================================
// EDGE FUNCTION: google-oauth-callback
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

        if (error) {
            return errorPage('Authorization Failed', error)
        }

        if (!code || !state) {
            return errorPage('Invalid Request', 'Missing code or state parameter')
        }

        let userId: string
        try {
            const stateData = JSON.parse(atob(state))
            userId = stateData.userId
        } catch {
            return errorPage('Invalid State', 'Could not decode state parameter')
        }

        const supabaseAdmin = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
        )

        const clientId = Deno.env.get('GOOGLE_CLIENT_ID')!
        const clientSecret = Deno.env.get('GOOGLE_CLIENT_SECRET')!
        const supabaseUrl = Deno.env.get('SUPABASE_URL')!
        const redirectUri = `${supabaseUrl}/functions/v1/google-oauth-callback`

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

        const expiresAt = new Date(Date.now() + (tokens.expires_in * 1000))

        // Update mfd_profiles with Google data
        const { error: upsertError } = await supabaseAdmin
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

        if (upsertError) {
            console.error('Database error:', upsertError)
            return errorPage('Database Error', 'Failed to save tokens')
        }

        // Get user profile to check for existing sheet
        const { data: profile } = await supabaseAdmin
            .from('mfd_profiles')
            .select('*')
            .eq('user_id', userId)
            .single()

        console.log('Checking for existing sheet... google_sheet_id:', profile?.google_sheet_id)

        // Check 1: User already has sheet
        if (profile?.google_sheet_id) {
            console.log('User already has sheet:', profile.google_sheet_id)
            const sheetUrl = `https://docs.google.com/spreadsheets/d/${profile.google_sheet_id}/edit`
            const clientsUrl = profile.google_clients_folder_id 
                ? `https://drive.google.com/drive/folders/${profile.google_clients_folder_id}` 
                : null
            return successPage(email, sheetUrl, clientsUrl, 'Your sheet is ready!')
        }

        // Check 2: Same email already has sheet under different user - reuse it
        const { data: existingByEmail } = await supabaseAdmin
            .from('mfd_profiles')
            .select('user_id, google_sheet_id, google_drive_folder_id, google_clients_folder_id')
            .eq('google_email', email)
            .neq('user_id', userId)
            .not('google_sheet_id', 'is', null)
            .maybeSingle()

        if (existingByEmail?.google_sheet_id) {
            console.log('Found existing sheet for email:', email, '- Reusing:', existingByEmail.google_sheet_id)
            
            await supabaseAdmin
                .from('mfd_profiles')
                .update({
                    google_sheet_id: existingByEmail.google_sheet_id,
                    google_drive_folder_id: existingByEmail.google_drive_folder_id,
                    google_clients_folder_id: existingByEmail.google_clients_folder_id,
                    updated_at: new Date().toISOString(),
                })
                .eq('user_id', userId)
            
            const sheetUrl = `https://docs.google.com/spreadsheets/d/${existingByEmail.google_sheet_id}/edit`
            const clientsUrl = existingByEmail.google_clients_folder_id 
                ? `https://drive.google.com/drive/folders/${existingByEmail.google_clients_folder_id}` 
                : null
            return successPage(email, sheetUrl, clientsUrl, 'Your sheet is ready! (Reconnected)')
        }

        // ==================== CREATE NEW SHEET ====================

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

        // Store folder and sheet info
        console.log('Updating mfd_profiles with sheet ID:', newSheetId)
        const { error: updateError } = await supabaseAdmin
            .from('mfd_profiles')
            .update({
                google_drive_folder_id: mySheetsFolder.id,
                google_sheet_id: newSheetId,
                google_clients_folder_id: clientsFolder.id,
                updated_at: new Date().toISOString(),
            })
            .eq('user_id', userId)

        if (updateError) {
            console.error('Failed to update mfd_profiles:', updateError)
            return errorPage('Database Error', `Failed to save sheet: ${updateError.message}`)
        }

        console.log('Setup complete for user:', email)
        return successPage(email, sheetUrl, clientsUrl, 'Your sheet is ready! Auto-sync is enabled.')

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
    const successUrl = new URL('https://vercel-status-pages.vercel.app/google-connected.html')
    successUrl.searchParams.set('email', email)
    successUrl.searchParams.set('sheet', sheetUrl)
    if (clientsUrl) successUrl.searchParams.set('folder', clientsUrl)
    successUrl.searchParams.set('message', message)
    
    return new Response(null, {
        status: 302,
        headers: { 'Location': successUrl.toString() }
    })
}

// ==================== ERROR PAGE ====================
function errorPage(title: string, message: string) {
    const errorUrl = new URL('https://vercel-status-pages.vercel.app/google-error.html')
    errorUrl.searchParams.set('title', title)
    errorUrl.searchParams.set('message', message)
    
    return new Response(null, {
        status: 302,
        headers: { 'Location': errorUrl.toString() }
    })
}