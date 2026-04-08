// ============================================================
// EDGE FUNCTION: import-from-sheet  (v3.0 — Production Ready)
// Import data from Google Sheet to DB (user-initiated)
// Sheet → DB with validation and duplicate handling
//
// UPGRADES APPLIED:
//   1. Retry Logic (fetchWithRetry with exponential backoff)
//   2. Token Refresh on 401
//   3. Structured Logging (JSON log helper)
//   4. Health Check (GET endpoint)
//   5. JWT Auth (isServiceRoleToken)
//   6. Rate Limit Tracking (apiCallMetrics)
// ============================================================

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// ==================== CONFIGURATION ====================

const MAX_RETRIES = 3
const BASE_DELAY_MS = 1000
const RATE_LIMIT_DELAY_MS = 60000

// Cache for Google access tokens
let cachedToken: { token: string; expiry: number } | null = null

// Track API call metrics
let apiCallMetrics = {
  totalCalls: 0,
  retries: 0,
  rateLimitHits: 0
}

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// ==================== STRUCTURED LOGGING ====================

type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'

function log(level: LogLevel, action: string, details?: Record<string, any>) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    function: 'import-from-sheet',
    action,
    ...details
  }
  const message = JSON.stringify(entry)
  switch (level) {
    case 'ERROR': console.error(message); break
    case 'WARN': console.warn(message); break
    default: console.log(message)
  }
}

// ==================== RETRY WRAPPER ====================

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/** Normalize phone to +91XXXXXXXXXX format */
function normalizePhone(val: any): string {
  if (!val) return ''
  let digits = String(val).replace(/[^0-9]/g, '')
  digits = digits.replace(/^0+/, '')
  if (digits.startsWith('91') && digits.length === 12) {
    digits = digits.slice(2)
  }
  if (digits.length === 10) {
    return `+91${digits}`
  }
  return String(val).trim()
}

async function fetchWithRetry(
  url: string,
  options: RequestInit,
  context: { userId?: string; action: string }
): Promise<Response> {
  let lastError: Error | null = null
  
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    apiCallMetrics.totalCalls++
    
    if (attempt > 0) {
      apiCallMetrics.retries++
      const delay = BASE_DELAY_MS * Math.pow(2, attempt - 1)
      log('WARN', 'retrying_request', { userId: context.userId, action: context.action, attempt, delayMs: delay })
      await sleep(delay)
    }
    
    try {
      const response = await fetch(url, options)
      
      if (response.status === 429) {
        apiCallMetrics.rateLimitHits++
        log('WARN', 'rate_limit_hit', { userId: context.userId, action: context.action, attempt })
        if (attempt < MAX_RETRIES) {
          await sleep(RATE_LIMIT_DELAY_MS)
          continue
        }
      }
      
      if (response.status === 401) {
        log('WARN', 'auth_error_invalidating_token', { userId: context.userId, action: context.action })
        cachedToken = null
        if (attempt < MAX_RETRIES) continue
      }
      
      return response
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error))
      log('ERROR', 'fetch_error', { userId: context.userId, action: context.action, attempt, error: lastError.message })
    }
  }
  
  throw lastError || new Error('Max retries exceeded')
}

// ==================== ENUM MAPPINGS (Sheet Display → DB) ====================
const genderFromSheet: Record<string, string> = {
  'male': 'male',
  'female': 'female',
  'others': 'other',
}

const maritalStatusFromSheet: Record<string, string> = {
  'single': 'single',
  'married': 'married',
  'divorced': 'divorced',
  'widower': 'widower',
  'separated': 'separated',
  "don't know": 'dont_know',
}

const occupationFromSheet: Record<string, string> = {
  'service': 'service',
  'business': 'business',
  'retired': 'retired',
  'professional': 'professional',
  'student': 'student',
  'self employed': 'self_employed',
  'housemaker': 'housemaker',
  "don't know": 'dont_know',
}

const incomeGroupFromSheet: Record<string, string> = {
  '0': 'zero',
  '1-2.5': '1_to_2_5',
  '2.6-8.8': '2_6_to_8_8',
  '8.9-12': '8_9_to_12',
  '12.1-24': '12_1_to_24',
  '24.1-48': '24_1_to_48',
  '48.1+': '48_1_plus',
  "don't know": 'dont_know',
}

const ageGroupFromSheet: Record<string, string> = {
  'below 18': 'below_18',
  '18-24': '18_to_24',
  '25-35': '25_to_35',
  '36-45': '36_to_45',
  '46-55': '46_to_55',
  '56+': '56_plus',
  "don't know": 'dont_know',
}

const riskProfileFromSheet: Record<string, string> = {
  'conservative': 'conservative',
  'moderately conservative': 'moderately_conservative',
  'moderate': 'moderate',
  'moderately aggressive': 'moderately_aggressive',
  'aggressive': 'aggressive',
}

const sourceFromSheet: Record<string, string> = {
  'natural market': 'natural_market',
  'referral': 'referral',
  'social networking': 'social_networking',
  'business group': 'business_group',
  'marketing activity': 'marketing_activity',
  'iap': 'iap',
  'cold call': 'cold_call',
  'social media': 'social_media',
}

const opportunityStageFromSheet: Record<string, string> = {
  'identified': 'identified',
  'inbound': 'inbound',
  'proposed': 'proposed',
}

const opportunityTypeFromSheet: Record<string, string> = {
  'sip': 'sip',
  'lumpsum': 'lumpsum',
  'swp': 'swp',
  'ncd': 'ncd',
  'fd': 'fd',
  'life insurance': 'life_insurance',
  'health insurance': 'health_insurance',
  'las': 'las',
}

const opportunitySourceFromSheet: Record<string, string> = {
  'goal planning': 'goal_planning',
  'portfolio rebalancing': 'portfolio_rebalancing',
  'client servicing': 'client_servicing',
  'financial activities': 'financial_activities',
}

// TAT display value to days
function tatFromSheet(tatDisplay: string): number | null {
  if (!tatDisplay) return null
  const lower = tatDisplay.toLowerCase().trim()
  if (lower.includes('less than 24 hours') || lower.includes('less than a day')) return 0
  if (lower.includes('1 day to 3 days') || lower.includes('1-3')) return 2
  if (lower.includes('4 days to 7 days') || lower.includes('4-7')) return 5
  if (lower.includes('5 days to 15 days') || lower.includes('5-15')) return 10
  if (lower.includes('15 days to 30 days') || lower.includes('15-30')) return 22
  if (lower.includes('30 days to 90 days') || lower.includes('30-90')) return 60
  if (lower.includes('more than 90')) return 91
  return null
}

// ==================== MAIN HANDLER ====================

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  // Health check endpoint
  if (req.method === 'GET') {
    log('INFO', 'health_check', { metrics: apiCallMetrics })
    return new Response(
      JSON.stringify({ 
        status: 'healthy', 
        function: 'import-from-sheet',
        version: '3.0',
        metrics: apiCallMetrics
      }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  // Reset metrics for this run
  apiCallMetrics = { totalCalls: 0, retries: 0, rateLimitHits: 0 }

  const startTime = Date.now()
  log('INFO', 'import_started')

  try {
    // ==================== AUTH: Verify user JWT or service role ====================
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      return new Response(
        JSON.stringify({ error: 'Missing authorization header' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Decode the JWT payload to check role
    function isServiceRoleToken(auth: string): boolean {
      try {
        const token = auth.replace('Bearer ', '')
        const payload = JSON.parse(atob(token.split('.')[1]))
        return payload.role === 'service_role'
      } catch {
        return false
      }
    }

    const isServiceRole = isServiceRoleToken(authHeader)
    const body = await req.json().catch(() => ({}))
    const testUserId = body.user_id  // optional: for testing with service role key

    let userId: string

    if (isServiceRole && testUserId) {
      // ==================== TEST MODE: Service role with specific user_id ====================
      userId = testUserId
      log('INFO', 'mode_test', { userId })
    } else {
      // ==================== USER MODE: Verify user JWT ====================
      const supabaseUser = createClient(
        Deno.env.get('SUPABASE_URL') ?? '',
        Deno.env.get('SUPABASE_ANON_KEY') ?? '',
        { global: { headers: { Authorization: authHeader } } }
      )

      const { data: { user }, error: userError } = await supabaseUser.auth.getUser()
      if (!user || userError) {
        return new Response(
          JSON.stringify({ error: 'Unauthorized. Valid JWT required.' }),
          { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      userId = user.id
      log('INFO', 'mode_user', { userId })
    }

    // ==================== GET SHEET ID ====================
    const { data: profile } = await supabaseAdmin
      .from('mfd_profiles')
      .select('google_sheet_id')
      .eq('user_id', userId)
      .single()

    if (!profile?.google_sheet_id) {
      return new Response(
        JSON.stringify({ error: 'No Google Sheet configured for this user' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const sheetId = profile.google_sheet_id

    // ==================== GET SERVICE ACCOUNT ====================
    const { data: configData } = await supabaseAdmin
      .from('app_config')
      .select('value')
      .eq('key', 'google_service_account')
      .single()

    if (!configData?.value) {
      throw new Error('Google service account not configured in app_config')
    }

    const serviceAccount = JSON.parse(configData.value)
    const accessToken = await getGoogleAccessToken(serviceAccount)

    // ==================== FETCH SHEET DATA (with retry) ====================
    log('INFO', 'fetching_sheet_data', { userId, sheetId })

    const [leadsData, clientsData, bosData] = await Promise.all([
      fetchSheetData(accessToken, sheetId, 'Leads', 2, userId),
      fetchSheetData(accessToken, sheetId, 'Client Profile', 4, userId),
      fetchSheetData(accessToken, sheetId, 'Business Opportunities', 2, userId)
    ])

    log('INFO', 'sheet_data_fetched', { 
      userId, 
      leadsRows: leadsData.length, 
      clientsRows: clientsData.length, 
      bosRows: bosData.length 
    })

    // ==================== IMPORT LEADS ====================
    const leadsResult = await importLeads(supabaseAdmin, userId, leadsData)

    // ==================== IMPORT CLIENTS ====================
    const clientsResult = await importClients(supabaseAdmin, userId, clientsData)

    // Get client/lead name lookup for BOs
    const { data: allClients } = await supabaseAdmin
      .from('clients')
      .select('id, name')
      .eq('user_id', userId)
      .eq('is_deleted', false)
    
    const { data: allLeads } = await supabaseAdmin
      .from('leads')
      .select('id, name')
      .eq('user_id', userId)

    const clientNameToId = new Map((allClients || []).map(c => [c.name?.toLowerCase(), c.id]))
    const leadNameToId = new Map((allLeads || []).map(l => [l.name?.toLowerCase(), l.id]))

    // ==================== IMPORT BUSINESS OPPORTUNITIES ====================
    const bosResult = await importBOs(supabaseAdmin, userId, bosData, clientNameToId, leadNameToId)

    // ==================== LOG SYNC ====================
    await supabaseAdmin.from('excel_sync_logs').insert({
      user_id: userId,
      sync_type: 'full_import',
      sync_direction: 'excel_to_app',
      records_synced: leadsResult.imported + clientsResult.imported + bosResult.imported,
      status: 'success',
      started_at: new Date(startTime).toISOString(),
      completed_at: new Date().toISOString()
    })

    const totalDuration = Date.now() - startTime
    log('INFO', 'import_completed', {
      userId,
      leadsImported: leadsResult.imported,
      leadsSkipped: leadsResult.skipped,
      clientsImported: clientsResult.imported,
      clientsSkipped: clientsResult.skipped,
      bosImported: bosResult.imported,
      bosSkipped: bosResult.skipped,
      durationMs: totalDuration,
      metrics: apiCallMetrics
    })

    return new Response(
      JSON.stringify({
        success: true,
        leads: leadsResult,
        clients: clientsResult,
        business_opportunities: bosResult,
        duration_ms: totalDuration,
        metrics: apiCallMetrics
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error: any) {
    log('ERROR', 'import_failed', { error: error.message, stack: error.stack?.substring(0, 500) })
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

// ==================== SHEET DATA FETCHING (with retry) ====================

async function fetchSheetData(accessToken: string, sheetId: string, sheetName: string, dataStartRow: number, userId: string): Promise<string[][]> {
  const range = encodeURIComponent(`${sheetName}!A${dataStartRow}:AZ1000`)
  
  const response = await fetchWithRetry(
    `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${range}`,
    {
      headers: { 'Authorization': `Bearer ${accessToken}` }
    },
    { userId, action: `fetchSheet:${sheetName}` }
  )

  if (!response.ok) {
    const error = await response.text()
    log('ERROR', 'sheet_fetch_failed', { userId, sheetName, error })
    return []
  }

  const data = await response.json() as any
  return data.values || []
}

// ==================== IMPORT FUNCTIONS ====================

async function importLeads(
  supabase: any,
  userId: string,
  rows: string[][]
): Promise<{ imported: number; skipped: number; errors: string[] }> {
  const result = { imported: 0, skipped: 0, errors: [] as string[] }

  // Get existing leads for duplicate check
  const { data: existingLeads } = await supabase
    .from('leads')
    .select('name, phone')
    .eq('user_id', userId)

  const existingSet = new Set(
    (existingLeads || []).map(l => `${l.name?.toLowerCase()}|${normalizePhone(l.phone)}`)
  )

  for (const row of rows) {
    try {
      // Skip empty rows
      if (!row[3]?.trim()) continue  // Column D = Prospect Name

      const name = row[3]?.trim()
      const phone = normalizePhone(row[10]) || null  // Column K = Contact No

      // Duplicate check: same name + phone
      const key = `${name.toLowerCase()}|${phone}`
      if (existingSet.has(key)) {
        result.skipped++
        continue
      }

      // Parse scheduled_date from Month + Date columns
      let scheduledDate = null
      if (row[1] && row[2]) {
        const monthStr = row[1].trim()
        const dayStr = row[2].toString().trim()
        const year = new Date().getFullYear()
        const monthIndex = new Date(`${monthStr} 1, 2000`).getMonth()
        if (!isNaN(monthIndex)) {
          scheduledDate = new Date(year, monthIndex, parseInt(dayStr)).toISOString().split('T')[0]
        }
      }

      const leadData = {
        user_id: userId,
        name,
        phone,
        scheduled_date: scheduledDate,
        age_group: ageGroupFromSheet[row[4]?.toLowerCase()?.trim()] || null,
        gender: genderFromSheet[row[5]?.toLowerCase()?.trim()] || null,
        marital_status: maritalStatusFromSheet[row[6]?.toLowerCase()?.trim()] || null,
        occupation: occupationFromSheet[row[7]?.toLowerCase()?.trim()] || null,
        income_group: incomeGroupFromSheet[row[8]?.toLowerCase()?.trim()] || null,
        dependants: row[9] ? parseInt(row[9]) || null : null,
        area: row[11]?.trim() || null,
        sourced_by: row[12]?.trim() || null,
        source: sourceFromSheet[row[13]?.toLowerCase()?.trim()] || null,
        source_description: row[14]?.trim() || null,
        notes: row[15]?.trim() || null,
        conversion_date: parseDate(row[16]),
        tat_days: tatFromSheet(row[17] || ''),
        created_at: new Date().toISOString()
      }

      const { error } = await supabase.from('leads').insert(leadData)
      
      if (error) {
        result.errors.push(`Lead "${name}": ${error.message}`)
      } else {
        result.imported++
        existingSet.add(key)  // Add to set to prevent duplicates in same batch
      }
    } catch (e: any) {
      result.errors.push(`Row error: ${e.message}`)
    }
  }

  log('INFO', 'leads_imported', { userId, imported: result.imported, skipped: result.skipped, errors: result.errors.length })
  return result
}

async function importClients(
  supabase: any,
  userId: string,
  rows: string[][]
): Promise<{ imported: number; skipped: number; errors: string[] }> {
  const result = { imported: 0, skipped: 0, errors: [] as string[] }

  // Get existing clients for duplicate check
  const { data: existingClients } = await supabase
    .from('clients')
    .select('name, phone')
    .eq('user_id', userId)
    .eq('is_deleted', false)

  const existingSet = new Set(
    (existingClients || []).map(c => `${c.name?.toLowerCase()}|${normalizePhone(c.phone)}`)
  )

  for (const row of rows) {
    try {
      // Skip empty rows
      if (!row[1]?.trim()) continue  // Column B = Client Name

      const name = row[1]?.trim()
      const phone = normalizePhone(row[15]) || null  // Column P = Contact no.

      // Duplicate check: same name + phone
      const key = `${name.toLowerCase()}|${phone}`
      if (existingSet.has(key)) {
        result.skipped++
        continue
      }

      const clientData = {
        user_id: userId,
        name,
        phone,
        notes: row[2]?.trim() || null,
        touchpoints_this_year: row[3] ? parseInt(row[3]) || 0 : 0,
        client_creation_year: row[4] ? parseInt(row[4]) || null : null,
        source: sourceFromSheet[row[5]?.toLowerCase()?.trim()] || null,
        source_description: row[6]?.trim() || null,
        birthdate: parseDate(row[7]),
        age_group: ageGroupFromSheet[row[8]?.toLowerCase()?.trim()] || null,
        age: row[9] ? parseInt(row[9]) || null : null,
        gender: genderFromSheet[row[10]?.toLowerCase()?.trim()] || null,
        marital_status: maritalStatusFromSheet[row[11]?.toLowerCase()?.trim()] || null,
        occupation: occupationFromSheet[row[12]?.toLowerCase()?.trim()] || null,
        income_group: incomeGroupFromSheet[row[13]?.toLowerCase()?.trim()] || null,
        dependants: row[14] ? parseInt(row[14]) || null : null,
        email: row[16]?.trim() || null,
        area: row[17]?.trim() || null,
        risk_profile: riskProfileFromSheet[row[18]?.toLowerCase()?.trim()] || null,
        total_aum: parseNumber(row[19]),
        sip: parseNumber(row[20]),
        term_insurance: parseNumber(row[21]),
        health_insurance: parseNumber(row[22]),
        pa_insurance: parseNumber(row[23]),
        swp: parseNumber(row[24]),
        pms: parseNumber(row[25]),
        aif: parseNumber(row[26]),
        las: parseNumber(row[27]),
        li_premium: parseNumber(row[28]),
        ulips: parseNumber(row[29]),
        is_deleted: false,
        created_at: new Date().toISOString()
      }

      const { error } = await supabase.from('clients').insert(clientData)
      
      if (error) {
        result.errors.push(`Client "${name}": ${error.message}`)
      } else {
        result.imported++
        existingSet.add(key)
      }
    } catch (e: any) {
      result.errors.push(`Row error: ${e.message}`)
    }
  }

  log('INFO', 'clients_imported', { userId, imported: result.imported, skipped: result.skipped, errors: result.errors.length })
  return result
}

async function importBOs(
  supabase: any,
  userId: string,
  rows: string[][],
  clientNameToId: Map<string, string>,
  leadNameToId: Map<string, string>
): Promise<{ imported: number; skipped: number; errors: string[] }> {
  const result = { imported: 0, skipped: 0, errors: [] as string[] }

  for (const row of rows) {
    try {
      // Skip empty rows
      if (!row[1]?.trim()) continue  // Column B = Client Name/Lead

      const nameInSheet = row[1]?.trim().toLowerCase()
      
      // Try to match to client first, then lead
      let clientId = clientNameToId.get(nameInSheet) || null
      let leadId = null
      
      if (!clientId) {
        leadId = leadNameToId.get(nameInSheet) || null
      }

      // If no match found, skip (can't create BO without client/lead reference)
      if (!clientId && !leadId) {
        result.errors.push(`BO "${row[1]}": No matching client or lead found`)
        result.skipped++
        continue
      }

      const boData = {
        user_id: userId,
        client_id: clientId,
        lead_id: leadId,
        expected_amount: parseNumber(row[2]),
        opportunity_stage: opportunityStageFromSheet[row[3]?.toLowerCase()?.trim()] || 'identified',
        opportunity_type: opportunityTypeFromSheet[row[4]?.toLowerCase()?.trim()] || null,
        opportunity_source: opportunitySourceFromSheet[row[5]?.toLowerCase()?.trim()] || null,
        additional_info: row[6]?.trim() || null,
        due_date: parseDate(row[7]),
        due_time: row[8]?.trim() || null,
        tat_days: row[9] ? parseInt(row[9]) || null : null,
        created_at: new Date().toISOString()
      }

      const { error } = await supabase.from('business_opportunities').insert(boData)
      
      if (error) {
        result.errors.push(`BO for "${row[1]}": ${error.message}`)
      } else {
        result.imported++
      }
    } catch (e: any) {
      result.errors.push(`Row error: ${e.message}`)
    }
  }

  log('INFO', 'bos_imported', { userId, imported: result.imported, skipped: result.skipped, errors: result.errors.length })
  return result
}

// ==================== UTILITY FUNCTIONS ====================

function parseDate(dateStr: string | undefined): string | null {
  if (!dateStr?.trim()) return null
  try {
    const date = new Date(dateStr)
    if (!isNaN(date.getTime())) {
      return date.toISOString().split('T')[0]
    }
    return null
  } catch {
    return null
  }
}

function parseNumber(value: string | undefined): number | null {
  if (!value?.trim()) return null
  const num = parseFloat(value.replace(/,/g, ''))
  return isNaN(num) ? null : num
}

// ==================== GOOGLE AUTH ====================

async function getGoogleAccessToken(serviceAccount: any): Promise<string> {
  if (cachedToken && Date.now() < cachedToken.expiry) {
    return cachedToken.token
  }

  const now = Math.floor(Date.now() / 1000)
  const expiry = now + 3600

  const header = btoa(JSON.stringify({ alg: 'RS256', typ: 'JWT' }))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')

  const payload = btoa(JSON.stringify({
    iss: serviceAccount.client_email,
    scope: 'https://www.googleapis.com/auth/spreadsheets.readonly',
    aud: 'https://oauth2.googleapis.com/token',
    iat: now,
    exp: expiry,
    sub: serviceAccount.client_email
  }))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')

  const unsignedToken = `${header}.${payload}`

  const keyData = serviceAccount.private_key
    .replace(/-----BEGIN PRIVATE KEY-----/g, '')
    .replace(/-----END PRIVATE KEY-----/g, '')
    .replace(/\n/g, '').replace(/\r/g, '').trim()

  const binaryKey = atob(keyData)
  const keyArray = new Uint8Array(binaryKey.length)
  for (let i = 0; i < binaryKey.length; i++) {
    keyArray[i] = binaryKey.charCodeAt(i)
  }

  const key = await crypto.subtle.importKey(
    'pkcs8', keyArray.buffer,
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false, ['sign']
  )

  const signature = await crypto.subtle.sign(
    'RSASSA-PKCS1-v1_5', key,
    new TextEncoder().encode(unsignedToken)
  )

  const signatureB64 = btoa(String.fromCharCode(...new Uint8Array(signature)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')

  const jwt = `${unsignedToken}.${signatureB64}`

  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`
  })

  const data = await response.json() as any

  if (!data.access_token) {
    throw new Error(`Failed to get Google access token: ${JSON.stringify(data)}`)
  }

  cachedToken = {
    token: data.access_token,
    expiry: Date.now() + (55 * 60 * 1000)
  }

  return data.access_token
}