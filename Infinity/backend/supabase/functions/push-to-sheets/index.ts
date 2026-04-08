// ============================================================
// EDGE FUNCTION: push-to-sheets
// Receives data from DB trigger (pg_net) and pushes to Google Sheets
// Includes proper column mapping and ID-based row tracking
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
  table: string        // Target table (leads, clients, business_opportunities)
  rowData: Record<string, any>
  isRetry?: boolean
}

// Cache for Google access tokens (valid for 1 hour)
let cachedToken: { token: string; expiry: number } | null = null

// Column mappings for each sheet type
const columnMappings: { [key: string]: { [dbField: string]: string } } = {
  'leads': {
    'id': 'Sr No',
    'name': 'Prospect Name',
    'phone': 'Contact No',
    'gender': 'Gender',
    'marital_status': 'Marital Status',
    'occupation': 'Occupation',
    'age_group': 'Age Group',
    'income_group': 'Income Group',
    'dependants': 'Dependants',
    'area': 'Area',
    'sourced_by': 'Sourced By',
    'source': 'Source of Data',
    'source_description': 'Source Description',
    'remarks': 'Remarks'
  },
  'clients': {
    'id': 'Sr No',
    'name': 'Client Name',
    'phone': 'Contact no.',
    'email': 'Email ID',
    'gender': 'Gender',
    'marital_status': 'Marital Status',
    'occupation': 'Occupation',
    'age_group': 'Age Group',
    'age': 'Age',
    'birthdate': 'Birthdate',
    'income_group': 'Income Group',
    'dependants': 'Dependants',
    'source': 'Source',
    'source_description': 'Source Description',
    'area': 'Area'
  },
  'business_opportunities': {
    'client_name': 'Client Name/Lead',
    'expected_amount': 'Expected Amount',
    'stage': 'Opportunity Stage',
    'opportunity_type': 'Opportunity Type',
    'identified_from': 'Opportunity Identified From',
    'additional_info': 'Additional Info',
    'due_date': 'Due Date'
  }
}

// Header row configuration for each sheet
const headerRowMap: { [key: string]: number } = {
  'Leads': 1,
  'Client Profile': 3,
  'Business Opportunities': 1
}

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
    
    // Map table names to actual sheet names in Google Sheet
    const sheetNameMap: { [key: string]: string } = {
      'clients': 'Client Profile',
      'leads': 'Leads',
      'business_opportunities': 'Business Opportunities'
    }
    
    const sheetName = sheetNameMap[table] || table.charAt(0).toUpperCase() + table.slice(1)

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
    const headerRow = headerRowMap[sheetName] || 1
    const headers = await getSheetHeaders(accessToken, sheetId, sheetName, headerRow)

    if (!headers || headers.length === 0) {
      throw new Error(`Could not read headers from sheet ${sheetName}`)
    }

    // ==================== FIND NEXT EMPTY ROW ====================
    // Get all data in the sheet to find the actual next empty row
    const allDataRange = encodeURIComponent(`${sheetName}!A:A`)
    const allDataResponse = await fetch(
      `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${allDataRange}`,
      {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      }
    )
    
    if (!allDataResponse.ok) {
      throw new Error('Failed to read sheet data')
    }
    
    const allData = await allDataResponse.json()
    const allRows = allData.values || []
    
    // First data row is after header
    // Find the first completely empty row after header
    let targetRow = headerRow + 1
    for (let i = headerRow; i < allRows.length; i++) {
      const row = allRows[i]
      // Check if row has any data in first column
      if (!row || !row[0] || row[0].toString().trim() === '') {
        targetRow = i + 1  // +1 because array is 0-indexed but sheets are 1-indexed
        break
      }
    }
    
    // If we didn't find an empty row, append at the end
    if (targetRow <= headerRow) {
      targetRow = allRows.length + 1
    }

    // ==================== BUILD ROW VALUES WITH PROPER MAPPING ====================
    const mapping = columnMappings[table] || {}
    
    // Build row with explicit values for ALL columns (including empty ones)
    const rowValues = headers.map(header => {
      // Leave Sr No blank to allow auto-increment in sheets
      if (header === 'Sr No' || header === 'Sr No.') {
        return ''
      }

      // Find which database field maps to this header
      let dbValue = ''
      for (const [dbField, sheetCol] of Object.entries(mapping)) {
        if (sheetCol === header) {
          const rawValue = rowData[dbField]
          dbValue = formatValue(rawValue)
          break
        }
      }

      return dbValue  // Will be '' if no mapping found (explicitly empty, not copied)
    })

    // ==================== WRITE TO GOOGLE SHEETS ====================
    // Use PUT to write to specific row (not append, to avoid auto-fill issues)
    const updateRange = `${sheetName}!A${targetRow}:${columnIndexToLetter(headers.length)}${targetRow}`

    const updateResponse = await fetch(
      `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${encodeURIComponent(updateRange)}?valueInputOption=USER_ENTERED`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          range: updateRange,
          majorDimension: 'ROWS',
          values: [rowValues]
        })
      }
    )

    if (!updateResponse.ok) {
      const errorText = await updateResponse.text()
      throw new Error(`Sheets API error: ${updateResponse.status} - ${errorText}`)
    }

    // ==================== LOG SUCCESS ====================
    const duration = Date.now() - startTime
    console.log(`Successfully synced ${table} record ${id} to row ${targetRow} in ${duration}ms`)

    return new Response(
      JSON.stringify({
        success: true,
        table,
        recordId: id,
        updatedRow: targetRow,
        duration_ms: duration
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Push to sheets error:', error)

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

  const now = Math.floor(Date.now() / 1000)
  const expiry = now + 3600
  
  // Create JWT with proper base64url encoding
  const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
    
  const payload = btoa(JSON.stringify({
    iss: serviceAccount.client_email,
    scope: 'https://www.googleapis.com/auth/spreadsheets',
    aud: 'https://oauth2.googleapis.com/token',
    iat: now,
    exp: expiry,
    sub: serviceAccount.client_email
  }))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
    
  const unsignedToken = `${header}.${payload}`
  
  // Clean private key
  const keyData = serviceAccount.private_key
    .replace(/-----BEGIN PRIVATE KEY-----/g, '')
    .replace(/-----END PRIVATE KEY-----/g, '')
    .replace(/\n/g, '')
    .replace(/\r/g, '')
    .trim()
    
  // Convert to binary
  const binaryKey = atob(keyData)
  const keyArray = new Uint8Array(binaryKey.length)
  for (let i = 0; i < binaryKey.length; i++) {
    keyArray[i] = binaryKey.charCodeAt(i)
  }
  
  // Import and sign
  const key = await crypto.subtle.importKey(
    'pkcs8',
    keyArray.buffer,
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['sign']
  )
  
  const signature = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5',
    key,
    new TextEncoder().encode(unsignedToken)
  )
  
  // Convert signature to base64url
  const signatureB64 = btoa(String.fromCharCode(...new Uint8Array(signature)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
    
  const jwt = `${unsignedToken}.${signatureB64}`
  
  // Exchange for access token
  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`
  })
  
  const data = await response.json() as any
  
  if (!data.access_token) {
    throw new Error(`Failed to get Google access token: ${JSON.stringify(data)}`)
  }

  // Cache the token
  cachedToken = {
    token: data.access_token,
    expiry: Date.now() + (55 * 60 * 1000)  // 55 minutes (5 min buffer)
  }

  return data.access_token
}

// ==================== SHEETS API HELPERS ====================

async function getSheetHeaders(accessToken: string, sheetId: string, sheetName: string, headerRow: number = 1): Promise<string[]> {
  const range = encodeURIComponent(`${sheetName}!${headerRow}:${headerRow}`)
  const response = await fetch(
    `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${range}`,
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



// ==================== UTILITY FUNCTIONS ====================

function formatValue(value: any): string {
  // Handle nulls
  if (value === null || value === undefined) return ''

  // Handle dates
  if (value instanceof Date) {
    return value.toISOString().split('T')[0]
  }

  // Handle ISO date strings
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
    return value.split('T')[0]
  }

  // Handle booleans
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }

  // Handle arrays/objects
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }

  // Convert to string and capitalize first letter for enum values
  let strValue = String(value).trim()
  
  // Capitalize enum values to match sheet dropdowns (male -> Male, service -> Service, etc.)
  if (strValue && strValue.length > 0) {
    strValue = strValue.charAt(0).toUpperCase() + strValue.slice(1).toLowerCase()
  }

  return strValue
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
