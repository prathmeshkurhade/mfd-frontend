// ============================================================
// EDGE FUNCTION: google-oauth-start
// Redirects user to Google OAuth consent screen
// Usage: GET /google-oauth-start?user_id=UUID
// ============================================================

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
    if (req.method === 'OPTIONS') {
        return new Response('ok', { headers: corsHeaders })
    }

    try {
        const url = new URL(req.url)

        // Get user_id from query params (for browser redirect)
        let userId = url.searchParams.get('user_id')

        // If no query param, try to get from JWT
        if (!userId) {
            const authHeader = req.headers.get('Authorization')
            if (authHeader) {
                const supabaseUser = createClient(
                    Deno.env.get('SUPABASE_URL') ?? '',
                    Deno.env.get('SUPABASE_ANON_KEY') ?? '',
                    { global: { headers: { Authorization: authHeader } } }
                )
                const { data: { user } } = await supabaseUser.auth.getUser()
                if (user) {
                    userId = user.id
                }
            }
        }

        // If still no userId, try request body
        if (!userId && req.method === 'POST') {
            try {
                const body = await req.json()
                userId = body.userId || body.user_id
            } catch {
                // ignore body parse error
            }
        }

        if (!userId) {
            return new Response(
                JSON.stringify({
                    error: 'Missing user_id parameter',
                    usage: 'Add ?user_id=YOUR_UUID to the URL'
                }),
                { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        // Get OAuth config from environment or database
        const clientId = Deno.env.get('GOOGLE_CLIENT_ID')
        const supabaseUrl = Deno.env.get('SUPABASE_URL')

        if (!clientId) {
            return new Response(
                JSON.stringify({ error: 'GOOGLE_CLIENT_ID not configured' }),
                { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        // Build redirect URI
        const redirectUri = `${supabaseUrl}/functions/v1/google-oauth-callback`

        // Build state with user info
        const state = btoa(JSON.stringify({ userId, timestamp: Date.now() }))

        // Required scopes for Drive and Sheets
        // Using full 'drive' scope to allow copying templates shared by others
        const scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/calendar.events'
        ].join(' ')

        // Build Google OAuth URL
        const oauthUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth')
        oauthUrl.searchParams.set('client_id', clientId)
        oauthUrl.searchParams.set('redirect_uri', redirectUri)
        oauthUrl.searchParams.set('response_type', 'code')
        oauthUrl.searchParams.set('scope', scopes)
        oauthUrl.searchParams.set('access_type', 'offline')
        oauthUrl.searchParams.set('prompt', 'consent')
        oauthUrl.searchParams.set('state', state)

        // Redirect directly to Google
        return new Response(null, {
            status: 302,
            headers: {
                'Location': oauthUrl.toString(),
                ...corsHeaders
            }
        })

    } catch (error) {
        console.error('Error:', error)
        return new Response(
            JSON.stringify({ error: error.message }),
            { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
    }
})
