// ============================================================
// EDGE FUNCTION: sync-sheet-snapshot  (v3.0 — Production Ready)
// Push current DB state to user's Google Sheet
// Called by cron (dirty users only, batched) or on-demand (single user)
// 
// UPGRADES APPLIED:
//   1. Dirty Flag System (sync_needed + BATCH_SIZE + last_synced_at)
//   2. Dropdown Preservation (applyDataValidation)
//   3. Retry Logic (fetchWithRetry with exponential backoff)
//   4. Token Refresh on 401
//   5. Structured Logging (JSON log helper)
//   6. Health Check (GET endpoint)
//   7. Bug Fixes (requestedMode, JWT auth)
//   8. Rate Limit Tracking (apiCallMetrics)
//   9. Queue depth reporting in response
// ============================================================

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

// ==================== CONFIGURATION ====================

const MAX_RETRIES = 3
const BASE_DELAY_MS = 1000
const RATE_LIMIT_DELAY_MS = 60000  // 1 minute wait on rate limit
const BATCH_SIZE = 10              // Max users per cron invocation

// Cache for Google access token
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
    function: 'sync-sheet-snapshot',
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

// ==================== ENUM MAPPINGS (DB → Sheet Display) ====================
const genderToSheet: Record<string, string> = {
  'male': 'Male',
  'female': 'Female',
  'other': 'Others',
}

const maritalStatusToSheet: Record<string, string> = {
  'single': 'Single',
  'married': 'Married',
  'divorced': 'Divorced',
  'widower': 'Widower',
  'separated': 'Separated',
  'dont_know': "Don't know",
}

const occupationToSheet: Record<string, string> = {
  'service': 'Service',
  'business': 'Business',
  'retired': 'Retired',
  'professional': 'Professional',
  'student': 'Student',
  'self_employed': 'Self Employed',
  'housemaker': 'Housemaker',
  'dont_know': "Don't know",
}

const incomeGroupToSheet: Record<string, string> = {
  'zero': '0',
  '1_to_2_5': '1-2.5',
  '2_6_to_8_8': '2.6-8.8',
  '8_9_to_12': '8.9-12',
  '12_1_to_24': '12.1-24',
  '24_1_to_48': '24.1-48',
  '48_1_plus': '48.1+',
  'dont_know': "don't know",
}

const ageGroupToSheet: Record<string, string> = {
  'below_18': 'below 18',
  '18_to_24': '18-24',
  '25_to_35': '25-35',
  '36_to_45': '36-45',
  '46_to_55': '46-55',
  '56_plus': '56+',
  'dont_know': "don't know",
}

const riskProfileToSheet: Record<string, string> = {
  'conservative': 'Conservative',
  'moderately_conservative': 'Moderately Conservative',
  'moderate': 'Moderate',
  'moderately_aggressive': 'Moderately Aggressive',
  'aggressive': 'Aggressive',
}

const sourceToSheet: Record<string, string> = {
  'natural_market': 'natural market',
  'referral': 'referral',
  'social_networking': 'social networking',
  'business_group': 'business group',
  'marketing_activity': 'marketing activity',
  'iap': 'iap',
  'cold_call': 'cold call',
  'social_media': 'social media',
}

const opportunityStageToSheet: Record<string, string> = {
  'identified': 'identified',
  'inbound': 'inbound',
  'proposed': 'proposed',
}

const opportunityTypeToSheet: Record<string, string> = {
  'sip': 'sip',
  'lumpsum': 'lumpsum',
  'swp': 'swp',
  'ncd': 'ncd',
  'fd': 'fd',
  'life_insurance': 'life insurance',
  'health_insurance': 'health insurance',
  'las': 'las',
}

const opportunitySourceToSheet: Record<string, string> = {
  'goal_planning': 'goal planning',
  'portfolio_rebalancing': 'portfolio rebalancing',
  'client_servicing': 'client servicing',
  'financial_activities': 'financial activities',
}

// TAT days to display value
function tatDaysToSheet(days: number | null): string {
  if (days === null || days === undefined) return ''
  if (days <= 0) return 'Less than 24 hours'
  if (days <= 3) return '1 day to 3 days'
  if (days <= 7) return '4 days to 7 days'
  if (days <= 15) return '5 days to 15 days'
  if (days <= 30) return '15 days to 30 days'
  if (days <= 90) return '30 days to 90 days'
  return 'More than 90 days'
}

// ==================== DATA VALIDATION DEFINITIONS ====================

interface DropdownConfig {
  column: number  // 0-indexed column
  values: string[]
}

const leadsDropdowns: DropdownConfig[] = [
  { column: 1, values: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'] },
  { column: 4, values: ['below 18', '18-24', '25-35', '36-45', '46-55', '56+', "don't know"] },
  { column: 5, values: ['Male', 'Female', 'Others'] },
  { column: 6, values: ['Single', 'Married', 'Divorced', 'Widower', 'Separated', "Don't know"] },
  { column: 7, values: ['Service', 'Business', 'Retired', 'Professional', 'Student', 'Self Employed', 'Housemaker', "Don't know"] },
  { column: 8, values: ['0', '1-2.5', '2.6-8.8', '8.9-12', '12.1-24', '24.1-48', '48.1+', "don't know"] },
  { column: 9, values: ['0', '1', '2', '3', '4', '5+'] },
  { column: 12, values: ['natural market', 'referral', 'social networking', 'business group', 'marketing activity', 'iap', 'cold call', 'social media'] },
  { column: 13, values: ['natural market', 'referral', 'social networking', 'business group', 'marketing activity', 'iap', 'cold call', 'social media'] },
  { column: 17, values: ['Less than 24 hours', '1 day to 3 days', '4 days to 7 days', '5 days to 15 days', '15 days to 30 days', '30 days to 90 days', 'More than 90 days'] },
]

const clientsDropdowns: DropdownConfig[] = [
  { column: 5, values: ['natural market', 'referral', 'social networking', 'business group', 'marketing activity', 'iap', 'cold call', 'social media'] },
  { column: 8, values: ['below 18', '18-24', '25-35', '36-45', '46-55', '56+', "don't know"] },
  { column: 10, values: ['Male', 'Female', 'Others'] },
  { column: 11, values: ['Single', 'Married', 'Divorced', 'Widower', 'Separated', "Don't know"] },
  { column: 12, values: ['Service', 'Business', 'Retired', 'Professional', 'Student', 'Self Employed', 'Housemaker', "Don't know"] },
  { column: 13, values: ['0', '1-2.5', '2.6-8.8', '8.9-12', '12.1-24', '24.1-48', '48.1+', "don't know"] },
  { column: 14, values: ['0', '1', '2', '3', '4', '5+'] },
  { column: 18, values: ['Conservative', 'Moderately Conservative', 'Moderate', 'Moderately Aggressive', 'Aggressive'] },
]

const bosDropdowns: DropdownConfig[] = [
  { column: 3, values: ['identified', 'inbound', 'proposed'] },
  { column: 4, values: ['sip', 'lumpsum', 'swp', 'ncd', 'fd', 'life insurance', 'health insurance', 'las'] },
  { column: 5, values: ['goal planning', 'portfolio rebalancing', 'client servicing', 'financial activities'] },
]

// ==================== RETRY WRAPPER ====================

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
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
        function: 'sync-sheet-snapshot',
        version: '3.0',
        metrics: apiCallMetrics
      }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  // Reset metrics for this run
  apiCallMetrics = { totalCalls: 0, retries: 0, rateLimitHits: 0 }

  const startTime = Date.now()
  log('INFO', 'sync_started')

  try {
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // ==================== PARSE REQUEST ====================
    const body = await req.json().catch(() => ({}))
    const requestedMode = body.mode  // can be 'cron', 'on_demand', or undefined
    const testUserId = body.user_id  // optional: for testing specific user with service role key

    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      return new Response(
        JSON.stringify({ error: 'Missing authorization header' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    let usersToSync: { userId: string; sheetId: string }[] = []
    
    // ==================== DETERMINE MODE ====================
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

    if (isServiceRole && testUserId) {
      // ==================== TEST MODE: Specific user with service role key ====================
      log('INFO', 'mode_test', { userId: testUserId })

      const { data: profile } = await supabaseAdmin
        .from('mfd_profiles')
        .select('google_sheet_id')
        .eq('user_id', testUserId)
        .single()

      if (!profile?.google_sheet_id) {
        return new Response(
          JSON.stringify({ error: 'No Google Sheet configured for this user' }),
          { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      usersToSync = [{ userId: testUserId, sheetId: profile.google_sheet_id }]

    } else if (requestedMode === 'cron' && isServiceRole) {
      // ==================== CRON MODE: Only dirty users, batched ====================
      // UPGRADE 1: Dirty flag — only sync users whose data actually changed
      const { data: profiles, error: profilesError } = await supabaseAdmin
        .from('mfd_profiles')
        .select('user_id, google_sheet_id')
        .eq('sync_needed', true)
        .not('google_sheet_id', 'is', null)
        .order('last_synced_at', { ascending: true, nullsFirst: true })
        .limit(BATCH_SIZE)

      if (profilesError) throw profilesError

      usersToSync = (profiles || []).map(p => ({
        userId: p.user_id,
        sheetId: p.google_sheet_id
      }))

      log('INFO', 'mode_cron', { dirtyUsers: usersToSync.length, batchSize: BATCH_SIZE })

    } else {
      // ==================== ON-DEMAND MODE: Single user ====================
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

      const { data: profile } = await supabaseAdmin
        .from('mfd_profiles')
        .select('google_sheet_id')
        .eq('user_id', user.id)
        .single()

      if (!profile?.google_sheet_id) {
        return new Response(
          JSON.stringify({ error: 'No Google Sheet configured for this user' }),
          { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      usersToSync = [{ userId: user.id, sheetId: profile.google_sheet_id }]
      log('INFO', 'mode_on_demand', { userId: user.id })
    }

    // ==================== EARLY EXIT: No dirty users in cron mode ====================
    if (usersToSync.length === 0) {
      log('INFO', 'sync_completed_no_dirty_users')
      return new Response(
        JSON.stringify({
          success: true,
          mode: requestedMode || 'on_demand',
          batch_size: 0,
          users_synced: 0,
          remaining_in_queue: 0,
          details: [],
          duration_ms: Date.now() - startTime,
          metrics: apiCallMetrics
        }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

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

    // ==================== SYNC EACH USER ====================
    const results: Array<{
      userId: string
      leads: number
      clients: number
      bos: number
      status: string
      error?: string
    }> = []

    for (const { userId, sheetId } of usersToSync) {
      const userStartTime = Date.now()
      
      try {
        // Timeout check — skip remaining users if running long
        if (Date.now() - startTime > 25000 && results.length > 0) {
          log('WARN', 'timeout_skipping_user', { userId })
          results.push({ userId, leads: 0, clients: 0, bos: 0, status: 'skipped', error: 'Timeout' })
          continue
        }

        // Rate limit awareness — pause if approaching limits
        if (apiCallMetrics.totalCalls > 0 && apiCallMetrics.totalCalls % 50 === 0) {
          log('WARN', 'rate_limit_pause', { callCount: apiCallMetrics.totalCalls })
          await sleep(5000)
        }

        // Get sheet tab IDs for data validation
        const sheetTabIds = await getSheetTabIds(accessToken, sheetId, userId)

        // Fetch all data for this user
        const [leadsResult, clientsResult, bosResult] = await Promise.all([
          supabaseAdmin.from('leads').select('*').eq('user_id', userId),
          supabaseAdmin.from('clients').select('*').eq('user_id', userId).eq('is_deleted', false),
          supabaseAdmin.from('business_opportunities').select('*').eq('user_id', userId)
        ])

        const leads = leadsResult.data || []
        const clients = clientsResult.data || []
        const bos = bosResult.data || []

        // Create client/lead name lookup for BOs
        const clientNameMap = new Map<string, string>(clients.map((c: any) => [c.id, c.name]))
        const leadNameMap = new Map<string, string>(leads.map((l: any) => [l.id, l.name]))

        log('INFO', 'syncing_user', { userId, leads: leads.length, clients: clients.length, bos: bos.length })

        // ==================== SYNC ALL THREE SHEETS ====================
        await syncLeadsSheet(accessToken, sheetId, leads, sheetTabIds, userId)
        await syncClientsSheet(accessToken, sheetId, clients, sheetTabIds, userId)
        await syncBOsSheet(accessToken, sheetId, bos, clientNameMap, leadNameMap, sheetTabIds, userId)

        // ==================== CLEAR DIRTY FLAG after successful sync ====================
        await supabaseAdmin
          .from('mfd_profiles')
          .update({ 
            sync_needed: false, 
            last_synced_at: new Date().toISOString() 
          })
          .eq('user_id', userId)

        // Log success
        await supabaseAdmin.from('excel_sync_logs').insert({
          user_id: userId,
          sync_type: 'full_snapshot',
          sync_direction: 'app_to_excel',
          records_synced: leads.length + clients.length + bos.length,
          status: 'success',
          started_at: new Date(userStartTime).toISOString(),
          completed_at: new Date().toISOString()
        })

        const userDuration = Date.now() - userStartTime
        log('INFO', 'user_sync_complete', { userId, leads: leads.length, clients: clients.length, bos: bos.length, durationMs: userDuration })

        results.push({
          userId,
          leads: leads.length,
          clients: clients.length,
          bos: bos.length,
          status: 'success'
        })

        // Add delay between users in cron mode to avoid rate limits
        if (requestedMode === 'cron' && usersToSync.length > 1) {
          await sleep(2000)
        }

      } catch (userError: any) {
        log('ERROR', 'user_sync_error', { userId, error: userError.message, stack: userError.stack?.substring(0, 500) })
        
        await supabaseAdmin.from('excel_sync_logs').insert({
          user_id: userId,
          sync_type: 'full_snapshot',
          sync_direction: 'app_to_excel',
          records_synced: 0,
          status: 'failed',
          error_message: userError.message,
          started_at: new Date(userStartTime).toISOString(),
          completed_at: new Date().toISOString()
        })

        results.push({
          userId,
          leads: 0,
          clients: 0,
          bos: 0,
          status: 'failed',
          error: userError.message
        })
      }
    }

    // ==================== COUNT REMAINING QUEUE (cron mode) ====================
    let remainingInQueue = 0
    if (requestedMode === 'cron') {
      const { count } = await supabaseAdmin
        .from('mfd_profiles')
        .select('*', { count: 'exact', head: true })
        .eq('sync_needed', true)
        .not('google_sheet_id', 'is', null)
      remainingInQueue = count || 0
    }

    log('INFO', 'sync_completed', { 
      mode: requestedMode || 'on_demand',
      totalUsers: results.length,
      successful: results.filter(r => r.status === 'success').length,
      failed: results.filter(r => r.status === 'failed').length,
      remainingInQueue,
      durationMs: Date.now() - startTime,
      metrics: apiCallMetrics
    })

    return new Response(
      JSON.stringify({
        success: true,
        mode: requestedMode || 'on_demand',
        batch_size: usersToSync.length,
        users_synced: results.filter(r => r.status === 'success').length,
        remaining_in_queue: remainingInQueue,
        details: results,
        duration_ms: Date.now() - startTime,
        metrics: apiCallMetrics
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error: any) {
    log('ERROR', 'sync_failed', { error: error.message, stack: error.stack?.substring(0, 500) })
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

// ==================== SHEET SYNC FUNCTIONS ====================

async function syncLeadsSheet(accessToken: string, sheetId: string, leads: any[], sheetTabIds: Map<string, number>, userId: string) {
  const sheetName = 'Leads'
  const dataStartRow = 2

  await clearSheetData(accessToken, sheetId, sheetName, dataStartRow, userId)

  if (leads.length === 0) {
    await applyDataValidation(accessToken, sheetId, sheetTabIds.get(sheetName), leadsDropdowns, dataStartRow, userId)
    return
  }

  const rows = leads.map((lead, index) => [
    index + 1,
    lead.scheduled_date ? new Date(lead.scheduled_date).toLocaleDateString('en-US', { month: 'long' }) : '',
    lead.scheduled_date ? new Date(lead.scheduled_date).getDate() : '',
    lead.name || '',
    ageGroupToSheet[lead.age_group] || '',
    genderToSheet[lead.gender] || '',
    maritalStatusToSheet[lead.marital_status] || '',
    occupationToSheet[lead.occupation] || '',
    incomeGroupToSheet[lead.income_group] || '',
    lead.dependants ?? '',
    lead.phone || '',
    lead.area || '',
    lead.sourced_by || '',
    sourceToSheet[lead.source] || '',
    lead.source_description || '',
    lead.notes || '',
    lead.conversion_date ? formatDate(lead.conversion_date) : '',
    tatDaysToSheet(lead.tat_days),
  ])

  await writeToSheet(accessToken, sheetId, sheetName, dataStartRow, rows, userId)
  await applyDataValidation(accessToken, sheetId, sheetTabIds.get(sheetName), leadsDropdowns, dataStartRow, userId)
}

async function syncClientsSheet(accessToken: string, sheetId: string, clients: any[], sheetTabIds: Map<string, number>, userId: string) {
  const sheetName = 'Client Profile'
  const dataStartRow = 4

  await clearSheetData(accessToken, sheetId, sheetName, dataStartRow, userId)

  if (clients.length === 0) {
    await applyDataValidation(accessToken, sheetId, sheetTabIds.get(sheetName), clientsDropdowns, dataStartRow, userId)
    return
  }

  const rows = clients.map((client, index) => [
    index + 1,
    client.name || '',
    client.notes || '',
    client.touchpoints_this_year ?? '',
    client.client_creation_year ?? '',
    sourceToSheet[client.source] || '',
    client.source_description || '',
    client.birthdate ? formatDate(client.birthdate) : '',
    ageGroupToSheet[client.age_group] || '',
    client.age ?? '',
    genderToSheet[client.gender] || '',
    maritalStatusToSheet[client.marital_status] || '',
    occupationToSheet[client.occupation] || '',
    incomeGroupToSheet[client.income_group] || '',
    client.dependants ?? '',
    client.phone || '',
    client.email || '',
    client.area || '',
    riskProfileToSheet[client.risk_profile] || '',
    client.total_aum ?? '',
    client.sip ?? '',
    client.term_insurance ?? '',
    client.health_insurance ?? '',
    client.pa_insurance ?? '',
    client.swp ?? '',
    client.pms ?? '',
    client.aif ?? '',
    client.las ?? '',
    client.li_premium ?? '',
    client.ulips ?? '',
    '',  // Cash surplus (goal link - read only)
    '',  // Retirement (goal link - read only)
    '',  // Child Education (goal link - read only)
    '',  // Other (goal link - read only)
  ])

  await writeToSheet(accessToken, sheetId, sheetName, dataStartRow, rows, userId)
  await applyDataValidation(accessToken, sheetId, sheetTabIds.get(sheetName), clientsDropdowns, dataStartRow, userId)
}

async function syncBOsSheet(
  accessToken: string, 
  sheetId: string, 
  bos: any[],
  clientNameMap: Map<string, string>,
  leadNameMap: Map<string, string>,
  sheetTabIds: Map<string, number>,
  userId: string
) {
  const sheetName = 'Business Opportunities'
  const dataStartRow = 2

  await clearSheetData(accessToken, sheetId, sheetName, dataStartRow, userId)

  if (bos.length === 0) {
    await applyDataValidation(accessToken, sheetId, sheetTabIds.get(sheetName), bosDropdowns, dataStartRow, userId)
    return
  }

  const rows = bos.map((bo, index) => {
    let nameValue = ''
    if (bo.client_id && clientNameMap.has(bo.client_id)) {
      nameValue = clientNameMap.get(bo.client_id) || ''
    } else if (bo.lead_id && leadNameMap.has(bo.lead_id)) {
      nameValue = leadNameMap.get(bo.lead_id) || ''
    }

    return [
      index + 1,
      nameValue,
      bo.expected_amount ?? '',
      opportunityStageToSheet[bo.opportunity_stage] || '',
      opportunityTypeToSheet[bo.opportunity_type] || '',
      opportunitySourceToSheet[bo.opportunity_source] || '',
      bo.additional_info || '',
      bo.due_date ? formatDate(bo.due_date) : '',
      bo.due_time || '',
      bo.tat_days ?? '',
    ]
  })

  await writeToSheet(accessToken, sheetId, sheetName, dataStartRow, rows, userId)
  await applyDataValidation(accessToken, sheetId, sheetTabIds.get(sheetName), bosDropdowns, dataStartRow, userId)
}

// ==================== GOOGLE SHEETS API HELPERS ====================

async function getSheetTabIds(accessToken: string, sheetId: string, userId: string): Promise<Map<string, number>> {
  const response = await fetchWithRetry(
    `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}?fields=sheets(properties(sheetId,title))`,
    {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${accessToken}` }
    },
    { userId, action: 'getSheetTabIds' }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to get sheet metadata: ${error}`)
  }

  const data = await response.json()
  const tabIds = new Map<string, number>()
  
  for (const sheet of data.sheets || []) {
    tabIds.set(sheet.properties.title, sheet.properties.sheetId)
  }

  log('DEBUG', 'sheet_tabs_loaded', { userId, tabs: Array.from(tabIds.keys()) })
  return tabIds
}

async function clearSheetData(accessToken: string, sheetId: string, sheetName: string, fromRow: number, userId: string) {
  const range = encodeURIComponent(`${sheetName}!A${fromRow}:AZ1000`)
  
  const response = await fetchWithRetry(
    `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${range}:clear`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    },
    { userId, action: `clearSheet:${sheetName}` }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to clear sheet ${sheetName}: ${error}`)
  }
}

async function writeToSheet(accessToken: string, sheetId: string, sheetName: string, startRow: number, rows: any[][], userId: string) {
  if (rows.length === 0) return

  const endCol = columnIndexToLetter(rows[0].length)
  const endRow = startRow + rows.length - 1
  const range = encodeURIComponent(`${sheetName}!A${startRow}:${endCol}${endRow}`)

  const response = await fetchWithRetry(
    `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${range}?valueInputOption=USER_ENTERED`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        range: `${sheetName}!A${startRow}:${endCol}${endRow}`,
        majorDimension: 'ROWS',
        values: rows
      })
    },
    { userId, action: `writeSheet:${sheetName}` }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to write to sheet ${sheetName}: ${error}`)
  }
}

async function applyDataValidation(
  accessToken: string,
  sheetId: string,
  tabId: number | undefined,
  dropdowns: DropdownConfig[],
  dataStartRow: number,
  userId: string
) {
  if (tabId === undefined) {
    log('WARN', 'missing_tab_id_for_validation', { userId })
    return
  }

  const requests = dropdowns.map(dropdown => ({
    setDataValidation: {
      range: {
        sheetId: tabId,
        startRowIndex: dataStartRow - 1,  // 0-indexed
        endRowIndex: 1000,
        startColumnIndex: dropdown.column,
        endColumnIndex: dropdown.column + 1
      },
      rule: {
        condition: {
          type: 'ONE_OF_LIST',
          values: dropdown.values.map(v => ({ userEnteredValue: v }))
        },
        showCustomUi: true,
        strict: false
      }
    }
  }))

  const response = await fetchWithRetry(
    `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}:batchUpdate`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ requests })
    },
    { userId, action: 'applyDataValidation' }
  )

  if (!response.ok) {
    const error = await response.text()
    log('WARN', 'data_validation_failed', { userId, error })
  } else {
    log('DEBUG', 'data_validation_applied', { userId, dropdownCount: dropdowns.length })
  }
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`
  } catch {
    return dateStr
  }
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
    scope: 'https://www.googleapis.com/auth/spreadsheets',
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