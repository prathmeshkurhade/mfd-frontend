// ============================================================
// EDGE FUNCTION: check-user-setup
// Returns user's Google OAuth and Sheet setup status
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
        // Get user from JWT
        const authHeader = req.headers.get('Authorization')
        if (!authHeader) {
            return new Response(
                JSON.stringify({ error: 'Missing authorization header' }),
                { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        const supabaseUser = createClient(
            Deno.env.get('SUPABASE_URL') ?? '',
            Deno.env.get('SUPABASE_ANON_KEY') ?? '',
            { global: { headers: { Authorization: authHeader } } }
        )

        const { data: { user }, error: userError } = await supabaseUser.auth.getUser()

        if (!user || userError) {
            return new Response(
                JSON.stringify({ error: 'Unauthorized' }),
                { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
            )
        }

        const userId = user.id
        const supabaseUrl = Deno.env.get('SUPABASE_URL')!

        // Initialize admin client for reading data
        const supabaseAdmin = createClient(
            supabaseUrl,
            Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
        )

        // Check MFD Profile for Google connection and sheet
        const { data: profile } = await supabaseAdmin
            .from('mfd_profiles')
            .select('*')
            .eq('user_id', userId)
            .single()

        const isConnected = !!profile?.google_connected
        const hasSheet = !!profile?.google_sheet_id

        const response: Record<string, unknown> = {
            isConnected,
            hasSheet,
            status: isConnected && hasSheet ? 'ready' : 'setup_required',
        }

        // Add OAuth URL if not connected
        if (!isConnected) {
            response.oauthUrl = `${supabaseUrl}/functions/v1/google-oauth-start?user_id=${userId}`
        }

        // Add connected Google email
        if (isConnected && profile) {
            response.googleEmail = profile.google_email
            response.connectedAt = profile.created_at
        }

        // Add sheet info if exists
        if (hasSheet && profile) {
            response.sheet = {
                id: profile.google_sheet_id,
                url: `https://docs.google.com/spreadsheets/d/${profile.google_sheet_id}/edit`,
                name: `${profile.name || profile.google_email?.split('@')[0] || 'My'} - Infinity Sheet`,
            }
        }

        return new Response(
            JSON.stringify(response),
            { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )

    } catch (error) {
        console.error('Error:', error)
        return new Response(
            JSON.stringify({ error: (error as Error).message }),
            { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
    }
})
