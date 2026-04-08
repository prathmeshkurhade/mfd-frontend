// ============================================================
// EDGE FUNCTION: sync-calendar-events (v2.0)
// Processes calendar event queue and syncs to Google Calendar
// Called by cron every minute or on-demand
//
// Flow:
//   1. Fetch pending items from calendar_event_queue
//   2. For each item, create/update/delete Google Calendar event
//   3. Store google_event_id back on the source row
//   4. Mark queue item as processed
// ============================================================

import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const BATCH_SIZE = 20
const MAX_RETRIES = 3

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// ==================== ENUM DISPLAY MAPPINGS ====================

const ENUM_DISPLAY: Record<string, Record<string, string>> = {
  // Task enums
  task_priority: {
    high: 'High',
    medium: 'Medium',
    low: 'Low'
  },
  task_status: {
    pending: 'Pending',
    completed: 'Completed',
    cancelled: 'Cancelled',
    carried_forward: 'Carried Forward'
  },
  task_medium: {
    call: 'Call',
    whatsapp: 'WhatsApp',
    email: 'Email',
    in_person: 'In Person',
    video_call: 'Video Call'
  },
  // Touchpoint enums
  interaction_type: {
    meeting_office: 'Meeting (Office)',
    meeting_home: 'Meeting (Home)',
    cafe: 'Cafe',
    restaurant: 'Restaurant',
    call: 'Call',
    video_call: 'Video Call'
  },
  touchpoint_status: {
    scheduled: 'Scheduled',
    completed: 'Completed',
    cancelled: 'Cancelled',
    rescheduled: 'Rescheduled'
  },
  // Business Opportunity enums
  opportunity_stage: {
    identified: 'Identified',
    inbound: 'Inbound',
    proposed: 'Proposed'
  },
  opportunity_type: {
    sip: 'SIP',
    lumpsum: 'Lumpsum',
    swp: 'SWP',
    ncd: 'NCD',
    fd: 'FD',
    life_insurance: 'Life Insurance',
    health_insurance: 'Health Insurance',
    las: 'LAS'
  },
  opportunity_source: {
    goal_planning: 'Goal Planning',
    portfolio_rebalancing: 'Portfolio Rebalancing',
    client_servicing: 'Client Servicing',
    financial_activities: 'Financial Activities'
  },
  bo_outcome: {
    open: 'Open',
    won: 'Won',
    lost: 'Lost'
  },
  // Lead enums
  lead_status: {
    follow_up: 'Follow Up',
    meeting_scheduled: 'Meeting Scheduled',
    cancelled: 'Cancelled',
    converted: 'Converted'
  },
  source: {
    natural_market: 'Natural Market',
    referral: 'Referral',
    social_networking: 'Social Networking',
    business_group: 'Business Group',
    marketing_activity: 'Marketing Activity',
    iap: 'IAP',
    cold_call: 'Cold Call',
    social_media: 'Social Media'
  }
}

// Helper to format enum values for display
function formatEnum(enumType: string, value: string | null | undefined): string {
  if (!value) return ''
  const mapping = ENUM_DISPLAY[enumType]
  if (mapping && mapping[value]) {
    return mapping[value]
  }
  // Fallback: convert snake_case to Title Case
  return value.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

// ==================== STRUCTURED LOGGING ====================

type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'

function log(level: LogLevel, action: string, details?: Record<string, any>) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    function: 'sync-calendar-events',
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

// ==================== MAIN HANDLER ====================

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  // Health check
  if (req.method === 'GET') {
    return new Response(
      JSON.stringify({ status: 'healthy', function: 'sync-calendar-events', version: '2.0' }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }

  const startTime = Date.now()
  log('INFO', 'processing_started')

  try {
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Fetch pending queue items
    const { data: queueItems, error: queueError } = await supabaseAdmin
      .from('calendar_event_queue')
      .select('*')
      .eq('processed', false)
      .lt('retry_count', MAX_RETRIES)
      .order('created_at', { ascending: true })
      .limit(BATCH_SIZE)

    if (queueError) throw queueError

    if (!queueItems || queueItems.length === 0) {
      log('INFO', 'no_pending_items')
      return new Response(
        JSON.stringify({ success: true, processed: 0, duration_ms: Date.now() - startTime }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    log('INFO', 'queue_items_found', { count: queueItems.length })

    // Group by user for token efficiency
    const itemsByUser = new Map<string, typeof queueItems>()
    for (const item of queueItems) {
      const existing = itemsByUser.get(item.user_id) || []
      existing.push(item)
      itemsByUser.set(item.user_id, existing)
    }

    const results: Array<{ id: string; status: string; error?: string }> = []

    // Process each user's items
    for (const [userId, items] of itemsByUser) {
      // Get user's OAuth token from mfd_profiles
      const { data: profileData, error: profileError } = await supabaseAdmin
        .from('mfd_profiles')
        .select('google_access_token, google_refresh_token, google_token_expiry, google_connected')
        .eq('user_id', userId)
        .single()

      if (profileError || !profileData || !profileData.google_access_token) {
        log('WARN', 'no_oauth_token', { userId })
        // Mark all items for this user as failed
        for (const item of items) {
          await markQueueItem(supabaseAdmin, item.id, false, 'No Google OAuth token found')
          results.push({ id: item.id, status: 'failed', error: 'No OAuth token' })
        }
        continue
      }

      // Refresh token if expired
      let accessToken = profileData.google_access_token
      if (profileData.google_token_expiry && new Date(profileData.google_token_expiry) <= new Date()) {
        try {
          accessToken = await refreshAccessToken(profileData.google_refresh_token, supabaseAdmin, userId)
        } catch (e: any) {
          log('ERROR', 'token_refresh_failed', { userId, error: e.message })
          for (const item of items) {
            await markQueueItem(supabaseAdmin, item.id, false, 'Token refresh failed')
            results.push({ id: item.id, status: 'failed', error: 'Token refresh failed' })
          }
          continue
        }
      }

      // Process each item for this user
      for (const item of items) {
        try {
          await processQueueItem(supabaseAdmin, accessToken, item)
          await markQueueItem(supabaseAdmin, item.id, true)
          results.push({ id: item.id, status: 'success' })
        } catch (e: any) {
          log('ERROR', 'item_processing_failed', { 
            itemId: item.id, 
            entityType: item.entity_type, 
            action: item.action,
            error: e.message 
          })
          await markQueueItem(supabaseAdmin, item.id, false, e.message)
          results.push({ id: item.id, status: 'failed', error: e.message })
        }
      }
    }

    const successful = results.filter(r => r.status === 'success').length
    const failed = results.filter(r => r.status === 'failed').length

    log('INFO', 'processing_completed', { 
      processed: results.length,
      successful,
      failed,
      durationMs: Date.now() - startTime
    })

    return new Response(
      JSON.stringify({
        success: true,
        processed: results.length,
        successful,
        failed,
        details: results,
        duration_ms: Date.now() - startTime
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error: any) {
    log('ERROR', 'processing_failed', { error: error.message })
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})

// ==================== HELPER: Get Table Name ====================

function getTableName(entityType: string): string {
  // Normalize to table name (plural form)
  const typeMap: Record<string, string> = {
    'task': 'tasks',
    'tasks': 'tasks',
    'lead': 'leads',
    'leads': 'leads',
    'touchpoint': 'touchpoints',
    'touchpoints': 'touchpoints',
    'business_opportunity': 'business_opportunities',
    'business_opportunities': 'business_opportunities'
  }
  return typeMap[entityType] || entityType
}

// ==================== HELPER: Normalize Entity Type ====================

function normalizeEntityType(entityType: string): string {
  // Normalize to singular form for switch statements
  const typeMap: Record<string, string> = {
    'task': 'task',
    'tasks': 'task',
    'lead': 'lead',
    'leads': 'lead',
    'touchpoint': 'touchpoint',
    'touchpoints': 'touchpoint',
    'business_opportunity': 'business_opportunity',
    'business_opportunities': 'business_opportunity'
  }
  return typeMap[entityType] || entityType
}

// ==================== PROCESS SINGLE QUEUE ITEM ====================

async function processQueueItem(
  supabase: any,
  accessToken: string,
  item: {
    id: string
    user_id: string
    entity_type: string
    entity_id: string
    action: string
  }
) {
  const { entity_type, entity_id, action, user_id } = item

  const tableName = getTableName(entity_type)
  
  // For delete action, we might not have the row anymore, but we need the google_event_id
  if (action === 'delete') {
    // Try to get from the row first (soft delete case)
    const { data: entityData } = await supabase
      .from(tableName)
      .select('google_event_id')
      .eq('id', entity_id)
      .single()

    const eventId = entityData?.google_event_id

    if (eventId) {
      await deleteCalendarEvent(accessToken, eventId)
      log('INFO', 'event_deleted', { entityType: entity_type, entityId: entity_id, eventId })
      
      // Log the action
      await supabase.from('calendar_sync_logs').insert({
        user_id,
        entity_type,
        entity_id,
        action: 'delete',
        google_event_id: eventId,
        status: 'success'
      })
    }
    return
  }

  // For create/update, fetch full entity data
  const { data: entityData, error: entityError } = await supabase
    .from(tableName)
    .select('*')
    .eq('id', entity_id)
    .single()

  if (entityError || !entityData) {
    throw new Error(`Entity not found: ${tableName}/${entity_id}`)
  }

  // Resolve client/lead name for better event titles
  let clientName = ''
  let leadName = ''
  
  if (entityData.client_id) {
    const { data: client } = await supabase
      .from('clients')
      .select('name')
      .eq('id', entityData.client_id)
      .single()
    clientName = client?.name || ''
  }
  
  if (entityData.lead_id) {
    const { data: lead } = await supabase
      .from('leads')
      .select('name')
      .eq('id', entityData.lead_id)
      .single()
    leadName = lead?.name || ''
  }

  const event = buildCalendarEvent(entity_type, entityData, clientName, leadName)

  let googleEventId: string

  if (action === 'create' || !entityData.google_event_id) {
    // Create new event
    googleEventId = await createCalendarEvent(accessToken, event)
    log('INFO', 'event_created', { entityType: entity_type, entityId: entity_id, eventId: googleEventId })
  } else {
    // Update existing event
    googleEventId = entityData.google_event_id
    try {
      await updateCalendarEvent(accessToken, googleEventId, event)
      log('INFO', 'event_updated', { entityType: entity_type, entityId: entity_id, eventId: googleEventId })
    } catch (e: any) {
      // If event not found, create a new one
      if (e.message === 'EVENT_NOT_FOUND') {
        googleEventId = await createCalendarEvent(accessToken, event)
        log('INFO', 'event_recreated', { entityType: entity_type, entityId: entity_id, eventId: googleEventId })
      } else {
        throw e
      }
    }
  }

  // Store google_event_id back on the entity
  await supabase
    .from(tableName)
    .update({ google_event_id: googleEventId })
    .eq('id', entity_id)

  // Log the sync
  await supabase.from('calendar_sync_logs').insert({
    user_id,
    entity_type,
    entity_id,
    action,
    google_event_id: googleEventId,
    status: 'success'
  })
}

// ==================== BUILD CALENDAR EVENT ====================

function buildCalendarEvent(
  entityType: string,
  entity: any,
  clientName: string,
  leadName: string
): {
  summary: string
  description: string
  colorId: string
  start: { dateTime?: string; date?: string; timeZone: string }
  end: { dateTime?: string; date?: string; timeZone: string }
} {
  const timeZone = 'Asia/Kolkata' // IST for Indian MFDs
  let summary = ''
  let description = ''
  let colorId = '1' // Default: Lavender
  let startDate: string
  let startTime: string | null = null
  let isAllDay = false

  const personName = clientName || leadName || ''
  const formatAmount = (amt: any) => amt ? `₹${Number(amt).toLocaleString('en-IN')}` : ''

  const normalizedType = normalizeEntityType(entityType)

  // Color mapping:
  // 1=Lavender, 2=Sage, 3=Grape, 4=Flamingo, 5=Banana
  // 6=Tangerine, 7=Peacock, 8=Graphite, 9=Blueberry, 10=Basil, 11=Tomato

  switch (normalizedType) {
    case 'lead':
      summary = `Lead: ${entity.name}`
      colorId = '7' // Peacock (cyan/teal)
      description = [
        entity.phone ? `Phone: ${entity.phone}` : '',
        entity.area ? `Area: ${entity.area}` : '',
        entity.source ? `Source: ${formatEnum('source', entity.source)}` : '',
        entity.status ? `Status: ${formatEnum('lead_status', entity.status)}` : '',
        entity.notes ? `Notes: ${entity.notes}` : '',
      ].filter(Boolean).join('\n')
      startDate = entity.scheduled_date
      startTime = entity.scheduled_time
      isAllDay = entity.all_day || !startTime
      break

    case 'touchpoint':
      summary = `Touchpoint: ${personName}`
      colorId = '10' // Basil (green)
      description = [
        entity.interaction_type ? `Type: ${formatEnum('interaction_type', entity.interaction_type)}` : '',
        entity.purpose ? `Purpose: ${entity.purpose}` : '',
        entity.location ? `Location: ${entity.location}` : '',
        entity.status ? `Status: ${formatEnum('touchpoint_status', entity.status)}` : '',
      ].filter(Boolean).join('\n')
      startDate = entity.scheduled_date
      startTime = entity.scheduled_time
      isAllDay = !startTime
      break

    case 'business_opportunity':
      summary = `Business Opportunity: ${personName}`
      colorId = '6' // Tangerine (orange)
      description = [
        entity.opportunity_type ? `Type: ${formatEnum('opportunity_type', entity.opportunity_type)}` : '',
        entity.expected_amount ? `Amount: ${formatAmount(entity.expected_amount)}` : '',
        entity.opportunity_stage ? `Stage: ${formatEnum('opportunity_stage', entity.opportunity_stage)}` : '',
        entity.opportunity_source ? `Source: ${formatEnum('opportunity_source', entity.opportunity_source)}` : '',
        entity.outcome ? `Outcome: ${formatEnum('bo_outcome', entity.outcome)}` : '',
        entity.additional_info ? `Info: ${entity.additional_info}` : '',
      ].filter(Boolean).join('\n')
      startDate = entity.due_date
      startTime = entity.due_time
      isAllDay = !startTime
      break

    case 'task':
      summary = `Task: ${personName || 'General'}`
      colorId = '9' // Blueberry (blue)
      description = [
        entity.description ? `Description: ${entity.description}` : '',
        entity.priority ? `Priority: ${formatEnum('task_priority', entity.priority)}` : '',
        entity.medium ? `Medium: ${formatEnum('task_medium', entity.medium)}` : '',
        entity.status ? `Status: ${formatEnum('task_status', entity.status)}` : '',
        entity.product_type ? `Product: ${entity.product_type}` : '',
      ].filter(Boolean).join('\n')
      startDate = entity.due_date
      startTime = entity.due_time
      isAllDay = entity.all_day || !startTime
      break

    default:
      throw new Error(`Unknown entity type: ${entityType}`)
  }

  // Build start/end times
  if (isAllDay) {
    // All-day event
    const endDate = new Date(startDate)
    endDate.setDate(endDate.getDate() + 1)
    return {
      summary,
      description,
      colorId,
      start: { date: startDate, timeZone },
      end: { date: endDate.toISOString().split('T')[0], timeZone }
    }
  } else {
    // Timed event (default 1 hour duration)
    const startDateTime = `${startDate}T${startTime || '09:00:00'}`
    const endDateTime = new Date(new Date(startDateTime).getTime() + 60 * 60 * 1000)
      .toISOString()
      .replace('Z', '')
    return {
      summary,
      description,
      colorId,
      start: { dateTime: startDateTime, timeZone },
      end: { dateTime: endDateTime.split('.')[0], timeZone }
    }
  }
}

// ==================== GOOGLE CALENDAR API ====================

async function createCalendarEvent(accessToken: string, event: any): Promise<string> {
  const response = await fetch(
    'https://www.googleapis.com/calendar/v3/calendars/primary/events',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(event),
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to create calendar event: ${error}`)
  }

  const data = await response.json()
  return data.id
}

async function updateCalendarEvent(accessToken: string, eventId: string, event: any): Promise<void> {
  const response = await fetch(
    `https://www.googleapis.com/calendar/v3/calendars/primary/events/${eventId}`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(event),
    }
  )

  if (!response.ok) {
    const error = await response.text()
    // If event not found (404), treat as needing recreation
    if (response.status === 404) {
      throw new Error('EVENT_NOT_FOUND')
    }
    throw new Error(`Failed to update calendar event: ${error}`)
  }
}

async function deleteCalendarEvent(accessToken: string, eventId: string): Promise<void> {
  const response = await fetch(
    `https://www.googleapis.com/calendar/v3/calendars/primary/events/${eventId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    }
  )

  // 404 is okay for delete (already deleted)
  if (!response.ok && response.status !== 404) {
    const error = await response.text()
    throw new Error(`Failed to delete calendar event: ${error}`)
  }
}

// ==================== HELPERS ====================

async function markQueueItem(
  supabase: any, 
  itemId: string, 
  success: boolean, 
  errorMessage?: string
) {
  if (success) {
    await supabase
      .from('calendar_event_queue')
      .update({ 
        processed: true, 
        processed_at: new Date().toISOString() 
      })
      .eq('id', itemId)
  } else {
    // Get current retry count
    const { data } = await supabase
      .from('calendar_event_queue')
      .select('retry_count')
      .eq('id', itemId)
      .single()
    
    const newRetryCount = (data?.retry_count || 0) + 1
    
    await supabase
      .from('calendar_event_queue')
      .update({ 
        retry_count: newRetryCount,
        error_message: errorMessage,
        processed: newRetryCount >= MAX_RETRIES
      })
      .eq('id', itemId)
  }
}

async function refreshAccessToken(
  refreshToken: string,
  supabase: any,
  userId: string
): Promise<string> {
  const clientId = Deno.env.get('GOOGLE_CLIENT_ID')!
  const clientSecret = Deno.env.get('GOOGLE_CLIENT_SECRET')!

  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
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
  const expiresAt = new Date(Date.now() + data.expires_in * 1000).toISOString()

  // Update tokens in mfd_profiles
  await supabase
    .from('mfd_profiles')
    .update({
      google_access_token: data.access_token,
      google_token_expiry: expiresAt,
    })
    .eq('user_id', userId)

  return data.access_token
}