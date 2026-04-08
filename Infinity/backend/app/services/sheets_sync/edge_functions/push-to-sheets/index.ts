// ============================================================
// EDGE FUNCTION: push-to-sheets
// Receives data from DB trigger (pg_net) and pushes to Google Sheets
// ============================================================

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface PushPayload {
  id: string           // Record ID (UUID)
  userId: string
  table: string        // Target table (leads, clients, etc.)
  rowData: Record<string, any>
  isRetry?: boolean
}

// Cache for Google access tokens (valid for 1 hour)
let cachedToken: { token: string; expiry: number } | null = null

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const startTime = Date.now()
  let payload: PushPayload | null = null

  try {
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // ==================== VERIFY AUTH ====================
    const authHeader = req.headers.get('authorization')
    const expectedKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
    if (!authHeader || authHeader !== `Bearer ${expectedKey}`) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // ==================== PARSE REQUEST ====================
    payload = await req.json() as PushPayload
    const { id, userId, table, rowData, isRetry } = payload

    // Get user sheet info from mfd_profiles
    const { data: profile } = await supabaseAdmin
      .from('mfd_profiles')
      .select('google_sheet_id')
      .eq('user_id', userId)
      .single()

    if (!profile?.google_sheet_id) {
      throw new Error('User has no Google Sheet configured')
    }

    const sheetId = profile.google_sheet_id
    const sheetName = table.charAt(0).toUpperCase() + table.slice(1) // Simple mapping: leads -> Leads

    console.log(`Processing sync for record ${id} in ${sheetName}`)

    // ==================== GET GOOGLE SERVICE ACCOUNT ====================
    const { data: configData } = await supabaseAdmin
      .from('app_config')
      .select('value')
      .eq('key', 'google_service_account')
      .single()

    if (!configData?.value) {
      throw new Error('Google service account not configured')
    }

    const serviceAccount = JSON.parse(configData.value)

    // ==================== GET GOOGLE ACCESS TOKEN ====================
    const accessToken = await getGoogleAccessToken(serviceAccount)

    // ==================== GET SHEET HEADERS ====================
    const headers = await getSheetHeaders(accessToken, sheetId, sheetName)

    if (!headers || headers.length === 0) {
      throw new Error(`Could not read headers from sheet ${sheetName}`)
    }

    // ==================== MAP DATA TO COLUMNS ====================
    const rowValues = headers.map(header => {
      if (!header || header === '') return ''

      // Try mapping common names
      const value = rowData[header] || rowData[header.toLowerCase()] || rowData[header.replace(/ /g, '_').toLowerCase()]

      // Handle nulls
      if (value === null || value === undefined) return ''

      // Handle dates
      if (value instanceof Date) {
        return value.toISOString().split('T')[0]
      }

      // Handle date strings
      if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
        return value.split('T')[0]
      }

      return value
    })

    // ==================== DETERMINE ROW NUMBER ====================
    // Find existing row by ID or name if possible, otherwise append
    let targetRow = await findRowNumber(accessToken, sheetId, sheetName, rowData, headers)
      || await getNextEmptyRow(accessToken, sheetId, sheetName)

    // ==================== WRITE TO GOOGLE SHEETS ====================
    const range = `${sheetName}!A${targetRow}:${columnIndexToLetter(headers.length)}${targetRow}`

    const updateResponse = await fetch(
      `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${encodeURIComponent(range)}?valueInputOption=USER_ENTERED`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          range: range,
          majorDimension: 'ROWS',
          values: [rowValues]
        })
      }
    )

    if (!updateResponse.ok) {
      const errorText = await updateResponse.text()
      throw new Error(`Sheets API error: ${updateResponse.status} - ${errorText}`)
    }

    // ==================== LOG TO EXCEL SYNC LOG ====================
    const duration = Date.now() - startTime
    await supabaseAdmin.from('excel_sync_logs').insert({
      user_id: userId,
      sync_type: 'incremental',
      sync_direction: 'app_to_excel',
      records_synced: 1,
      status: 'success',
      started_at: new Date(startTime).toISOString(),
      completed_at: new Date().toISOString()
    })

    console.log(`Successfully pushed to ${sheetName} row ${targetRow} in ${duration}ms`)

    return new Response(
      JSON.stringify({
        success: true,
        updatedRow: targetRow,
        duration_ms: duration
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Push to sheets error:', error)

    if (payload?.userId) {
      const supabaseAdmin = createClient(
        Deno.env.get('SUPABASE_URL') ?? '',
        Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
      )

      // Log failure
      await supabaseAdmin.from('excel_sync_logs').insert({
        user_id: payload.userId,
        sync_type: 'incremental',
        sync_direction: 'app_to_excel',
        records_synced: 0,
        status: 'failed',
        error_message: error.message,
        started_at: new Date(startTime).toISOString(),
        completed_at: new Date().toISOString()
      })
    }

    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

// ==================== GOOGLE AUTH ====================

async function getGoogleAccessToken(serviceAccount: any): Promise<string> {
  // Check cache
  if (cachedToken && Date.now() < cachedToken.expiry) {
    return cachedToken.token
  }

  // Create JWT
  const now = Math.floor(Date.now() / 1000)
  const expiry = now + 3600  // 1 hour

  const header = { alg: 'RS256', typ: 'JWT' }
  const payload = {
    iss: serviceAccount.client_email,
    scope: 'https://www.googleapis.com/auth/spreadsheets',
    aud: 'https://oauth2.googleapis.com/token',
    iat: now,
    exp: expiry
  }

  // Encode header and payload
  const headerB64 = base64UrlEncode(JSON.stringify(header))
  const payloadB64 = base64UrlEncode(JSON.stringify(payload))
  const unsignedToken = `${headerB64}.${payloadB64}`

  // Sign with private key
  const privateKey = await crypto.subtle.importKey(
    'pkcs8',
    pemToArrayBuffer(serviceAccount.private_key),
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['sign']
  )

  const encoder = new TextEncoder()
  const signature = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5',
    privateKey,
    encoder.encode(unsignedToken)
  )

  const signatureB64 = base64UrlEncode(arrayBufferToString(signature))
  const jwt = `${unsignedToken}.${signatureB64}`

  // Exchange JWT for access token
  const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`
  })

  const tokenData = await tokenResponse.json()

  if (!tokenData.access_token) {
    throw new Error(`Failed to get Google access token: ${JSON.stringify(tokenData)}`)
  }

  // Cache the token
  cachedToken = {
    token: tokenData.access_token,
    expiry: Date.now() + (55 * 60 * 1000)  // 55 minutes (5 min buffer)
  }

  return tokenData.access_token
}

// ==================== SHEETS API HELPERS ====================

async function getSheetHeaders(accessToken: string, sheetId: string, sheetName: string): Promise<string[]> {
  const response = await fetch(
    `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${encodeURIComponent(sheetName)}!1:1`,
    {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to get headers: ${error}`)
  }

  const data = await response.json()
  return data.values?.[0] || []
}

async function findRowNumber(
  accessToken: string,
  sheetId: string,
  sheetName: string,
  rowData: Record<string, any>,
  headers: string[]
): Promise<number | null> {
  // Try to find by _rowNumber first
  if (rowData._rowNumber && rowData._rowNumber >= 2) {
    return rowData._rowNumber
  }

  // Try to find by first column match
  const firstColValue = rowData[headers[0]]
  if (!firstColValue) return null

  const response = await fetch(
    `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${encodeURIComponent(sheetName)}!A:A`,
    {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }
  )

  if (!response.ok) return null

  const data = await response.json()
  const values = data.values || []

  for (let i = 1; i < values.length; i++) {  // Skip header row
    if (values[i][0] == firstColValue) {
      return i + 1  // 1-indexed
    }
  }

  return null
}

async function getNextEmptyRow(accessToken: string, sheetId: string, sheetName: string): Promise<number> {
  const response = await fetch(
    `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${encodeURIComponent(sheetName)}!A:A`,
    {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    }
  )

  if (!response.ok) {
    return 2  // Default to row 2 (after header)
  }

  const data = await response.json()
  const values = data.values || []

  return values.length + 1
}

// ==================== UTILITY FUNCTIONS ====================

function base64UrlEncode(str: string): string {
  const encoder = new TextEncoder()
  const data = encoder.encode(str)
  return btoa(String.fromCharCode(...data))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}

function arrayBufferToString(buffer: ArrayBuffer): string {
  return String.fromCharCode(...new Uint8Array(buffer))
}

function pemToArrayBuffer(pem: string): ArrayBuffer {
  const b64 = pem
    .replace(/-----BEGIN PRIVATE KEY-----/, '')
    .replace(/-----END PRIVATE KEY-----/, '')
    .replace(/\n/g, '')
    .replace(/\r/g, '')

  const binary = atob(b64)
  const buffer = new ArrayBuffer(binary.length)
  const view = new Uint8Array(buffer)

  for (let i = 0; i < binary.length; i++) {
    view[i] = binary.charCodeAt(i)
  }

  return buffer
}

function columnIndexToLetter(index: number): string {
  let letter = ''
  let temp = index

  while (temp > 0) {
    const remainder = (temp - 1) % 26
    letter = String.fromCharCode(65 + remainder) + letter
    temp = Math.floor((temp - 1) / 26)
  }

  return letter || 'A'
}
