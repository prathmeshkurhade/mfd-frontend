// ============================================================
// EDGE FUNCTION: sheets-webhook
// Receives data from Google Sheets and syncs to proper CRM tables
// Supports: Leads, Client Profile, Business Opportunities
// ============================================================

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-webhook-secret',
}

interface WebhookPayload {
  sheetId: string
  sheetName: string
  rows: Record<string, any>[]
  timestamp: string
  changeType?: 'edit' | 'full_sync'
}

// Sheet name to table mapping
const SHEET_TABLE_MAP: Record<string, string> = {
  'Leads': 'leads',
  'Client Profile': 'clients',
  'Business Opportunities': 'business_opportunities',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const startTime = Date.now()

  try {
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // ==================== VERIFY WEBHOOK SECRET ====================
    const webhookSecret = req.headers.get('x-webhook-secret')

    const { data: configData } = await supabaseAdmin
      .from('app_config')
      .select('value')
      .eq('key', 'sheet_webhook_secret')
      .single()

    if (!configData || webhookSecret !== configData.value) {
      console.error('Invalid webhook secret')
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // ==================== PARSE REQUEST ====================
    const payload: WebhookPayload = await req.json()
    const { sheetId, sheetName, rows, timestamp, changeType } = payload

    if (!sheetId || !sheetName || !rows) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    console.log(`Received ${rows.length} rows from ${sheetName}`)

    // ==================== GET USER FROM SHEET ====================
    // Look up in mfd_profiles as per provided schema
    const { data: profile, error: profileError } = await supabaseAdmin
      .from('mfd_profiles')
      .select('user_id')
      .eq('google_sheet_id', sheetId)
      .single()

    if (profileError || !profile) {
      console.error('Sheet not registered in any MFD profile:', sheetId)
      return new Response(
        JSON.stringify({ error: 'Sheet not registered' }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const userId = profile.user_id

    // ==================== DETERMINE TARGET TABLE ====================
    const targetTable = SHEET_TABLE_MAP[sheetName]

    if (!targetTable) {
      console.log(`Unknown sheet: ${sheetName}, skipping sync`)
      return new Response(
        JSON.stringify({ success: true, message: 'Sheet not configured for sync', skipped: true }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // ==================== TRANSFORM & SYNC DATA ====================
    let syncedCount = 0

    if (targetTable === 'leads') {
      syncedCount = await syncLeads(supabaseAdmin, userId, rows)
    } else if (targetTable === 'clients') {
      syncedCount = await syncClients(supabaseAdmin, userId, rows)
    } else if (targetTable === 'business_opportunities') {
      syncedCount = await syncOpportunities(supabaseAdmin, userId, rows)
    } else if (targetTable === 'tasks') {
      syncedCount = await syncTasks(supabaseAdmin, userId, rows)
    }

    // ==================== LOG SUCCESS ====================
    const duration = Date.now() - startTime
    console.log(`Synced ${syncedCount} rows to ${targetTable} in ${duration}ms`)

    return new Response(
      JSON.stringify({ success: true, synced: syncedCount, table: targetTable }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Webhook error:', error)
    return new Response(
      JSON.stringify({ error: (error as Error).message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

// ==================== SYNC LEADS ====================
async function syncLeads(supabase: any, userId: string, rows: Record<string, any>[]): Promise<number> {
  const records = rows.map(row => ({
    user_id: userId,
    name: row['Prospect Name'] || row['Name'] || null,
    phone: String(row['Contact No'] || row['Phone'] || ''),
    email: row['Email'] || null,
    age_group: row['Age Group'] || null,
    gender: row['Gender'] || null,
    marital_status: row['Marital Status'] || null,
    occupation: row['Occupation'] || null,
    income_group: row['Income Group'] || null,
    dependants: parseNumber(row['Dependants']),
    area: row['Area'] || null,
    source: row['Source of Data'] || row['Source'] || 'natural_market',
    source_description: row['Source Description'] || null,
    sourced_by: row['Sourced By'] || null,
    status: row['Status'] || 'follow_up',
    notes: row['Remarks'] || row['Notes'] || null,
    scheduled_date: parseDate(row['Date'] || row['Scheduled Date']),
    tat_days: parseNumber(row['Turn Around Time (TAT)'] || row['TAT']),
  })).filter(r => r.name)

  if (records.length === 0) return 0

  await supabase.from('leads').delete().eq('user_id', userId)
  const { error } = await supabase.from('leads').insert(records)
  if (error) throw error

  return records.length
}

// ==================== SYNC CLIENTS ====================
async function syncClients(supabase: any, userId: string, rows: Record<string, any>[]): Promise<number> {
  const records = rows.map(row => ({
    user_id: userId,
    name: row['Client Name'] || row['Name'] || null,
    phone: String(row['Contact no.'] || row['Phone'] || ''),
    email: row['Email ID'] || row['Email'] || null,
    address: row['Address'] || null,
    area: row['Area'] || null,
    birthdate: parseDate(row['Birthdate']),
    gender: row['Gender'] || 'male',
    marital_status: row['Marital Status'] || null,
    occupation: row['Occupation'] || null,
    income_group: row['Income Group'] || null,
    dependants: parseNumber(row['Dependants']),
    risk_profile: row['Client Risk Profile'] || row['Risk Profile'] || null,
    source: row['Source'] || 'referral',
    source_description: row['Source Description'] || null,
    sourced_by: row['Sourced By'] || null,
    total_aum: parseDecimal(row['Total AUM of Client'] || row['Total AUM']),
    sip: parseDecimal(row['SIP']),
    term_insurance: parseDecimal(row['Term'] || row['Term Insurance']),
    health_insurance: parseDecimal(row['Health'] || row['Health Insurance']),
    pa_insurance: parseDecimal(row['PA (Personal Accident)'] || row['PA Insurance']),
    swp: parseDecimal(row['SWP']),
    corpus: parseDecimal(row['Corpus']),
    pms: parseDecimal(row['PMS']),
    aif: parseDecimal(row['AIF']),
    las: parseDecimal(row['LAS']),
    li_premium: parseDecimal(row['LI Premium (Savings Plan)'] || row['LI Premium']),
    ulips: parseDecimal(row['ULIPs']),
    notes: row['Notes'] || row['notes'] || null,
  })).filter(r => r.name)

  if (records.length === 0) return 0

  await supabase.from('clients').delete().eq('user_id', userId)
  const { error } = await supabase.from('clients').insert(records)
  if (error) throw error

  return records.length
}

// ==================== SYNC BUSINESS OPPORTUNITIES ====================
async function syncOpportunities(supabase: any, userId: string, rows: Record<string, any>[]): Promise<number> {
  const records = rows.map(row => ({
    user_id: userId,
    expected_amount: parseDecimal(row['Expected Amount']),
    opportunity_stage: row['Opportunity Stage'] || row['Stage'] || 'identified',
    opportunity_type: row['Opportunity Type'] || 'sip',
    opportunity_source: row['Opportunity Identified From'] || row['Source'] || 'client_servicing',
    additional_info: row['Additional Info'] || null,
    due_date: parseDate(row['Due Date']),
    tat_days: parseNumber(row['TAT'] || row['tat']),
  })).filter(r => r.expected_amount)

  if (records.length === 0) return 0

  await supabase.from('business_opportunities').delete().eq('user_id', userId)
  const { error } = await supabase.from('business_opportunities').insert(records)
  if (error) throw error

  return records.length
}

// ==================== SYNC TASKS ====================
async function syncTasks(supabase: any, userId: string, rows: Record<string, any>[]): Promise<number> {
  const records = rows.map(row => ({
    user_id: userId,
    description: row['Description'] || row['Task'] || null,
    medium: row['Medium'] || 'call',
    priority: row['Priority'] || 'medium',
    due_date: parseDate(row['Due Date']),
    status: row['Status'] || 'pending',
  })).filter(r => r.description && r.due_date)

  if (records.length === 0) return 0

  await supabase.from('tasks').delete().eq('user_id', userId)
  const { error } = await supabase.from('tasks').insert(records)
  if (error) throw error

  return records.length
}

// ==================== HELPER FUNCTIONS ====================
function parseNumber(val: any): number | null {
  if (val === null || val === undefined || val === '') return null
  const num = parseInt(String(val).replace(/[^0-9-]/g, ''))
  return isNaN(num) ? null : num
}

function parseDecimal(val: any): number | null {
  if (val === null || val === undefined || val === '') return null
  const num = parseFloat(String(val).replace(/[^0-9.-]/g, ''))
  return isNaN(num) ? null : num
}

function parseDate(val: any): string | null {
  if (!val || val === '') return null
  try {
    const date = new Date(val)
    if (isNaN(date.getTime())) return null
    return date.toISOString().split('T')[0]
  } catch {
    return null
  }
}
