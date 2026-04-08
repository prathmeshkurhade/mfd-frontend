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
    // Look up in mfd_profiles by spreadsheet ID (same as google_sheet_id from OAuth)
    console.log('Looking for sheet:', sheetId)
    
    // Try exact match first
    let { data: profile, error: profileError } = await supabaseAdmin
      .from('mfd_profiles')
      .select('user_id, google_sheet_id')
      .eq('google_sheet_id', sheetId)
      .single()

    if (profileError) {
      console.error('Profile query error:', profileError.code, profileError.message)
    }
    
    if (!profile) {
      console.error('Sheet not registered in any MFD profile:', sheetId)
      
      // Debug: Show what sheets are in database
      const { data: allProfiles } = await supabaseAdmin
        .from('mfd_profiles')
        .select('user_id, google_sheet_id, google_email')
        .limit(10)
      
      console.log('Sheets in database:', allProfiles?.map(p => ({ email: p.google_email, sheetId: p.google_sheet_id })))
      
      return new Response(
        JSON.stringify({ error: 'Sheet not registered', receivedSheetId: sheetId }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
    
    console.log('✅ Found profile for sheet:', sheetId)

    const userId = profile.user_id
    console.log('Found user:', userId, 'for sheet:', sheetId)

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
    phone: normalizePhone(row['Contact No'] || row['Phone'] || ''),
    email: row['Email'] || null,
    age_group: mapAgeGroup(row['Age Group']),
    gender: mapGender(row['Gender']),
    marital_status: mapMaritalStatus(row['Marital Status']),
    occupation: mapOccupation(row['Occupation']),
    income_group: mapIncomeGroup(row['Income Group']),
    dependants: parseNumber(row['Dependants']),
    area: row['Area'] || null,
    source: mapSource(row['Source of Data'] || row['Source']),
    source_description: row['Source Description'] || null,
    sourced_by: row['Sourced By'] || null,
    status: mapLeadStatus(row['Status']),
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
    phone: normalizePhone(row['Contact no.'] || row['Phone'] || ''),
    email: row['Email ID'] || row['Email'] || null,
    address: row['Address'] || null,
    area: row['Area'] || null,
    birthdate: parseDate(row['Birthdate']),
    gender: mapGender(row['Gender']),
    marital_status: mapMaritalStatus(row['Marital Status']),
    occupation: mapOccupation(row['Occupation']),
    income_group: mapIncomeGroup(row['Income Group']),
    dependants: parseNumber(row['Dependants']),
    risk_profile: mapRiskProfile(row['Client Risk Profile'] || row['Risk Profile']),
    source: mapSource(row['Source']),
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
  const records = [];
  
  for (const row of rows) {
    const expected_amount = parseDecimal(row['Expected Amount'])
    if (!expected_amount) continue; // Skip rows without amount
    
    // Look up client or lead by name
    const clientOrLeadName = row['Client Name/Lead'] || row['Client Name'] || row['Lead'];
    let client_id = null;
    let lead_id = null;
    
    if (clientOrLeadName) {
      // Try to find in clients first
      const { data: clientData } = await supabase
        .from('clients')
        .select('id')
        .eq('user_id', userId)
        .ilike('name', `%${clientOrLeadName}%`)
        .limit(1)
      
      if (clientData && clientData.length > 0) {
        client_id = clientData[0].id;
      } else {
        // Try to find in leads
        const { data: leadData } = await supabase
          .from('leads')
          .select('id')
          .eq('user_id', userId)
          .ilike('name', `%${clientOrLeadName}%`)
          .limit(1)
        
        if (leadData && leadData.length > 0) {
          lead_id = leadData[0].id;
        }
      }
    }
    
    records.push({
      user_id: userId,
      client_id: client_id,
      lead_id: lead_id,
      expected_amount: expected_amount,
      opportunity_stage: mapOpportunityStage(row['Opportunity Stage']),
      opportunity_type: mapOpportunityType(row['Opportunity Type']),
      opportunity_source: mapOpportunitySource(row['Opportunity Identified From']),
      additional_info: row['Additional Info'] || null,
      due_date: parseDate(row['Due Date']),
      tat_days: parseNumber(row['TAT'] || row['tat']),
    });
  }

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

// ==================== ENUM MAPPING FUNCTIONS ====================

// Normalize string for comparison (trim, lowercase, collapse spaces)
function normalize(val: any): string {
  return String(val).toLowerCase().trim().replace(/\s+/g, ' ')
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

// Map sheet age group values to enum (database format: no 'a' prefix)
function mapAgeGroup(val: any): string | null {
  if (!val) return null
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'below 18': 'below_18',
    'below18': 'below_18',
    'below_18': 'below_18',
    '18': '18_to_24',
    '18 to 24': '18_to_24',
    '18-24': '18_to_24',
    '18_to_24': '18_to_24',
    '18to24': '18_to_24',
    '25': '25_to_35',
    '25 to 35': '25_to_35',
    '25-35': '25_to_35',
    '25_to_35': '25_to_35',
    '25to35': '25_to_35',
    '36': '36_to_45',
    '36 to 45': '36_to_45',
    '36-45': '36_to_45',
    '36_to_45': '36_to_45',
    '36to45': '36_to_45',
    '46': '46_to_55',
    '46 to 55': '46_to_55',
    '46-55': '46_to_55',
    '46_to_55': '46_to_55',
    '46to55': '46_to_55',
    '56': '56_plus',
    '56+': '56_plus',
    '56 plus': '56_plus',
    '56_plus': '56_plus',
    'above 55': '56_plus',
    'above55': '56_plus',
    'dont know': 'dont_know',
    'dont_know': 'dont_know',
    'don\'t know': 'dont_know',
    'dontknow': 'dont_know',
  }
  const result = mapping[str]
  if (!result) {
    console.warn('Unknown age group value:', val, '-> normalized:', str)
  }
  return result || null
}

// Map sheet gender values to enum
function mapGender(val: any): string | null {
  if (!val) return null
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'male': 'male',
    'm': 'male',
    'female': 'female',
    'f': 'female',
    'woman': 'female',
    'others': 'other',
    'other': 'other',
    'o': 'other',
    'prefer not to say': 'other',
  }
  return mapping[str] || null
}

// Map sheet marital status to enum
function mapMaritalStatus(val: any): string | null {
  if (!val) return null
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'single': 'single',
    's': 'single',
    'unmarried': 'single',
    'married': 'married',
    'm': 'married',
    'wed': 'married',
    'divorced': 'divorced',
    'div': 'divorced',
    'widower': 'widower',
    'widow': 'widower',
    'wd': 'widower',
    'separated': 'separated',
    'sep': 'separated',
    'dont know': 'dont_know',
    'dont_know': 'dont_know',
    'don\'t know': 'dont_know',
    'dontknow': 'dont_know',
    'unknown': 'dont_know',
  }
  return mapping[str] || null
}

// Map sheet occupation to enum
function mapOccupation(val: any): string | null {
  if (!val) return null
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'service': 'service',
    'salaried': 'service',
    'employee': 'service',
    'job': 'service',
    'business': 'business',
    'self business': 'business',
    'entrepreneur': 'business',
    'owner': 'business',
    'retired': 'retired',
    'ret': 'retired',
    'pensioner': 'retired',
    'professional': 'professional',
    'prof': 'professional',
    'doctor': 'professional',
    'lawyer': 'professional',
    'engineer': 'professional',
    'student': 'student',
    'stud': 'student',
    'self employed': 'self_employed',
    'self_employed': 'self_employed',
    'selfemployed': 'self_employed',
    'self employed': 'self_employed',
    'freelance': 'self_employed',
    'housemaker': 'housemaker',
    'housewife': 'housemaker',
    'homemaker': 'housemaker',
    'househusband': 'housemaker',
    'dont know': 'dont_know',
    'dont_know': 'dont_know',
    'don\'t know': 'dont_know',
    'dontknow': 'dont_know',
    'unknown': 'dont_know',
  }
  return mapping[str] || null
}

// Map sheet income group to enum (NO l prefix)
function mapIncomeGroup(val: any): string | null {
  if (!val) return null
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'zero': 'zero',
    '0': 'zero',
    '1': '1_to_2_5',
    '1 to 2.5': '1_to_2_5',
    '1-2.5': '1_to_2_5',
    '1_to_2_5': '1_to_2_5',
    '1to25': '1_to_2_5',
    '2.6': '2_6_to_8_8',
    '2.6 to 8.8': '2_6_to_8_8',
    '2.6-8.8': '2_6_to_8_8',
    '2_6_to_8_8': '2_6_to_8_8',
    '2.6to88': '2_6_to_8_8',
    '8.9': '8_9_to_12',
    '8.9 to 12': '8_9_to_12',
    '8.9-12': '8_9_to_12',
    '8_9_to_12': '8_9_to_12',
    '8.9to12': '8_9_to_12',
    '12': '12_1_to_24',
    '12.1': '12_1_to_24',
    '12.1 to 24': '12_1_to_24',
    '12.1-24': '12_1_to_24',
    '12_1_to_24': '12_1_to_24',
    '12.1to24': '12_1_to_24',
    '24': '24_1_to_48',
    '24.1': '24_1_to_48',
    '24.1 to 48': '24_1_to_48',
    '24.1-48': '24_1_to_48',
    '24_1_to_48': '24_1_to_48',
    '24.1to48': '24_1_to_48',
    '48': '48_1_plus',
    '48.1': '48_1_plus',
    '48.1+': '48_1_plus',
    '48.1 plus': '48_1_plus',
    '48_1_plus': '48_1_plus',
    '48plus': '48_1_plus',
    '48.1plus': '48_1_plus',
    'dont know': 'dont_know',
    'dont_know': 'dont_know',
    'don\'t know': 'dont_know',
    'dontknow': 'dont_know',
    'unknown': 'dont_know',
  }
  return mapping[str] || null
}

// Map sheet source to enum
function mapSource(val: any): string | null {
  if (!val) return 'natural_market'
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'natural market': 'natural_market',
    'natural_market': 'natural_market',
    'naturalmarket': 'natural_market',
    'market': 'natural_market',
    'walk in': 'natural_market',
    'walkin': 'natural_market',
    'referral': 'referral',
    'ref': 'referral',
    'referred': 'referral',
    'social networking': 'social_networking',
    'social_networking': 'social_networking',
    'socialnetworking': 'social_networking',
    'networking': 'social_networking',
    'business group': 'business_group',
    'business_group': 'business_group',
    'businessgroup': 'business_group',
    'group': 'business_group',
    'business association': 'business_group',
    'marketing activity': 'marketing_activity',
    'marketing_activity': 'marketing_activity',
    'marketingactivity': 'marketing_activity',
    'marketing': 'marketing_activity',
    'campaign': 'marketing_activity',
    'iap': 'iap',
    'insurance advisor program': 'iap',
    'cold call': 'cold_call',
    'cold_call': 'cold_call',
    'coldcall': 'cold_call',
    'calling': 'cold_call',
    'tele calling': 'cold_call',
    'social media': 'social_media',
    'social_media': 'social_media',
    'socialmedia': 'social_media',
    'facebook': 'social_media',
    'instagram': 'social_media',
    'whatsapp': 'social_media',
  }
  return mapping[str] || 'natural_market'
}

// Map sheet risk profile to enum
function mapRiskProfile(val: any): string | null {
  if (!val) return null
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'conservative': 'conservative',
    'cons': 'conservative',
    'low risk': 'conservative',
    'moderately conservative': 'moderately_conservative',
    'moderately_conservative': 'moderately_conservative',
    'moderatelyconservative': 'moderately_conservative',
    'mod cons': 'moderately_conservative',
    'moderate': 'moderate',
    'med': 'moderate',
    'medium': 'moderate',
    'mid': 'moderate',
    'moderately aggressive': 'moderately_aggressive',
    'moderately_aggressive': 'moderately_aggressive',
    'moderatelyaggressive': 'moderately_aggressive',
    'mod agg': 'moderately_aggressive',
    'aggressive': 'aggressive',
    'agg': 'aggressive',
    'high risk': 'aggressive',
  }
  return mapping[str] || null
}

// Map sheet opportunity stage to enum
function mapOpportunityStage(val: any): string | null {
  if (!val) return 'identified'
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'identified': 'identified',
    'identify': 'identified',
    'inbound': 'inbound',
    'in bound': 'inbound',
    'proposed': 'proposed',
    'proposal': 'proposed',
  }
  return mapping[str] || 'identified'
}

// Map sheet opportunity type to enum
function mapOpportunityType(val: any): string | null {
  if (!val) return 'sip'
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'sip': 'sip',
    'systematic investment plan': 'sip',
    'lumpsum': 'lumpsum',
    'lump sum': 'lumpsum',
    'swp': 'swp',
    'systematic withdrawal plan': 'swp',
    'ncd': 'ncd',
    'fd': 'fd',
    'fixed deposit': 'fd',
    'life insurance': 'life_insurance',
    'life_insurance': 'life_insurance',
    'lifeinsurance': 'life_insurance',
    'health insurance': 'health_insurance',
    'health_insurance': 'health_insurance',
    'healthinsurance': 'health_insurance',
    'las': 'las',
  }
  return mapping[str] || 'sip'
}

// Map sheet opportunity source to enum
function mapOpportunitySource(val: any): string | null {
  if (!val) return 'client_servicing'
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'goal planning': 'goal_planning',
    'goal_planning': 'goal_planning',
    'goalplanning': 'goal_planning',
    'goal': 'goal_planning',
    'portfolio rebalancing': 'portfolio_rebalancing',
    'portfolio_rebalancing': 'portfolio_rebalancing',
    'portfoliorebalancing': 'portfolio_rebalancing',
    'rebalancing': 'portfolio_rebalancing',
    'portfolio': 'portfolio_rebalancing',
    'client servicing': 'client_servicing',
    'client_servicing': 'client_servicing',
    'clientservicing': 'client_servicing',
    'servicing': 'client_servicing',
    'financial activities': 'financial_activities',
    'financial_activities': 'financial_activities',
    'financialactivities': 'financial_activities',
    'activities': 'financial_activities',
    'financial': 'financial_activities',
  }
  return mapping[str] || 'client_servicing'
}

// Map sheet lead status to enum
function mapLeadStatus(val: any): string | null {
  if (!val) return 'follow_up'
  const str = normalize(val)
  const mapping: Record<string, string> = {
    'follow up': 'follow_up',
    'follow_up': 'follow_up',
    'followup': 'follow_up',
    'follow': 'follow_up',
    'pending': 'follow_up',
    'new': 'follow_up',
    'open': 'follow_up',
    'meeting scheduled': 'meeting_scheduled',
    'meeting_scheduled': 'meeting_scheduled',
    'meetingscheduled': 'meeting_scheduled',
    'appointment': 'meeting_scheduled',
    'scheduled': 'meeting_scheduled',
    'meeting': 'meeting_scheduled',
    'cancelled': 'cancelled',
    'cancel': 'cancelled',
    'rejected': 'cancelled',
    'declined': 'cancelled',
    'not interested': 'cancelled',
    'converted': 'converted',
    'convert': 'converted',
    'closed': 'converted',
    'won': 'converted',
    'success': 'converted',
    'completed': 'converted',
  }
  return mapping[str] || 'follow_up'
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
