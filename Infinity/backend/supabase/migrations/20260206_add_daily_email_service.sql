-- Migration: Add Daily Email Service (SOD/Midday/EOD)
-- Date: 2026-02-06
-- Purpose: PostgreSQL message queue + email scheduling + audit logging

-- ============================================================================
-- PART 1: pgmq Extension & Queues
-- ============================================================================

-- Enable pgmq extension (must be enabled in Supabase)
CREATE EXTENSION IF NOT EXISTS pgmq;

-- Create main queue for email jobs
SELECT pgmq.create('email_jobs');

-- Create dead letter queue for permanently failed messages
SELECT pgmq.create('email_jobs_dlq');

-- ============================================================================
-- PART 2: Email Logs Table (Audit + Deduplication)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.email_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  email_type varchar(50) NOT NULL,
  target_date date NOT NULL,
  recipient_email varchar(255) NOT NULL,
  subject varchar(500),
  status varchar(20) NOT NULL,
  resend_message_id varchar(255),
  error_message text,
  items_snapshot jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_email_logs_user ON public.email_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_date ON public.email_logs(target_date);
CREATE INDEX IF NOT EXISTS idx_email_logs_lookup ON public.email_logs(user_id, email_type, target_date, status);

-- Unique index for deduplication (prevent duplicate sends)
CREATE UNIQUE INDEX IF NOT EXISTS idx_email_logs_dedup 
  ON public.email_logs(user_id, email_type, target_date) 
  WHERE status = 'sent';

-- Row-level security
ALTER TABLE public.email_logs ENABLE ROW LEVEL SECURITY;

-- Service role can do everything
CREATE POLICY "service_role_all" ON public.email_logs
  FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Users can read their own logs
CREATE POLICY "users_read_own" ON public.email_logs
  FOR SELECT
  USING (auth.uid() = user_id);

-- ============================================================================
-- PART 3: Time/Date Helper Functions
-- ============================================================================

-- Get current time in IST timezone
CREATE OR REPLACE FUNCTION public.get_ist_time()
RETURNS TIME
LANGUAGE SQL
STABLE
AS $$
  SELECT (NOW() AT TIME ZONE 'Asia/Kolkata')::TIME;
$$;

-- Get current date in IST timezone
CREATE OR REPLACE FUNCTION public.get_ist_date()
RETURNS DATE
LANGUAGE SQL
STABLE
AS $$
  SELECT (NOW() AT TIME ZONE 'Asia/Kolkata')::DATE;
$$;

-- Check if current time is within a window (handles wrap-around)
CREATE OR REPLACE FUNCTION public.time_in_window(
  check_time TIME,
  window_start TIME,
  window_end TIME
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
AS $$
  SELECT CASE
    WHEN window_start < window_end THEN
      check_time >= window_start AND check_time < window_end
    ELSE
      check_time >= window_start OR check_time < window_end
  END;
$$;

-- ============================================================================
-- PART 4: User Selection Functions
-- ============================================================================

-- Morning email users (user's morning_schedule_time ± 15 min window)
CREATE OR REPLACE FUNCTION public.get_users_for_morning_email(
  window_minutes INTEGER DEFAULT 15
)
RETURNS TABLE (
  user_id UUID,
  user_email VARCHAR,
  user_name VARCHAR
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    p.user_id,
    p.google_email,
    p.name
  FROM mfd_profiles p
  WHERE p.google_email IS NOT NULL
    AND p.email_daily_enabled = true
    AND public.time_in_window(
      public.get_ist_time(),
      p.morning_schedule_time,
      p.morning_schedule_time + (window_minutes || ' minutes')::INTERVAL
    )
    AND NOT EXISTS (
      SELECT 1 FROM public.email_logs el
      WHERE el.user_id = p.user_id
        AND el.email_type = 'morning_planner'
        AND el.target_date = public.get_ist_date()
        AND el.status = 'sent'
    );
$$;

-- Midday email users (2:00 PM ± 15 min window, fixed for all)
CREATE OR REPLACE FUNCTION public.get_users_for_afternoon_email(
  window_minutes INTEGER DEFAULT 15
)
RETURNS TABLE (
  user_id UUID,
  user_email VARCHAR,
  user_name VARCHAR
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    p.user_id,
    p.google_email,
    p.name
  FROM mfd_profiles p
  WHERE p.google_email IS NOT NULL
    AND p.email_daily_enabled = true
    AND public.time_in_window(
      public.get_ist_time(),
      '14:00'::TIME,
      '14:00'::TIME + (window_minutes || ' minutes')::INTERVAL
    )
    AND NOT EXISTS (
      SELECT 1 FROM public.email_logs el
      WHERE el.user_id = p.user_id
        AND el.email_type = 'afternoon_progress'
        AND el.target_date = public.get_ist_date()
        AND el.status = 'sent'
    );
$$;

-- EOD email users (user's eod_schedule_time ± 15 min window)
CREATE OR REPLACE FUNCTION public.get_users_for_eod_email(
  window_minutes INTEGER DEFAULT 15
)
RETURNS TABLE (
  user_id UUID,
  user_email VARCHAR,
  user_name VARCHAR
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    p.user_id,
    p.google_email,
    p.name
  FROM mfd_profiles p
  WHERE p.google_email IS NOT NULL
    AND p.email_daily_enabled = true
    AND public.time_in_window(
      public.get_ist_time(),
      p.eod_schedule_time,
      p.eod_schedule_time + (window_minutes || ' minutes')::INTERVAL
    )
    AND NOT EXISTS (
      SELECT 1 FROM public.email_logs el
      WHERE el.user_id = p.user_id
        AND el.email_type = 'eod_summary'
        AND el.target_date = public.get_ist_date()
        AND el.status = 'sent'
    );
$$;

-- ============================================================================
-- PART 5: Data Fetching Function
-- ============================================================================

-- Get all email data for a user on a specific date
CREATE OR REPLACE FUNCTION public.get_email_daily_items(
  p_user_id UUID,
  p_date DATE
)
RETURNS JSON
LANGUAGE SQL
STABLE
AS $$
  SELECT JSON_BUILD_OBJECT(
    'tasks', COALESCE((
      SELECT JSON_AGG(task_row ORDER BY priority_order, due_time_order)
      FROM (
        SELECT 
          JSON_BUILD_OBJECT(
            'id', t.id,
            'description', t.description,
            'client_name', c.name,
            'due_time', t.due_time,
            'priority', t.priority,
            'status', t.status,
            'medium', t.medium,
            'product_type', t.product_type,
            'carry_forward_count', t.carry_forward_count,
            'original_date', t.original_date,
            'completed_at', t.completed_at
          ) as task_row,
          CASE t.priority::TEXT 
            WHEN 'urgent' THEN 1 
            WHEN 'high' THEN 2 
            WHEN 'medium' THEN 3 
            WHEN 'low' THEN 4 
            ELSE 5 
          END as priority_order,
          COALESCE(t.due_time, '23:59'::TIME) as due_time_order
        FROM tasks t
        LEFT JOIN clients c ON t.client_id = c.id
        WHERE t.user_id = p_user_id 
          AND t.due_date = p_date 
          AND (t.is_deleted IS NULL OR t.is_deleted = false)
      ) t
    ), '[]'::JSON),

    'touchpoints', COALESCE((
      SELECT JSON_AGG(tp_row ORDER BY time_order)
      FROM (
        SELECT 
          JSON_BUILD_OBJECT(
            'id', tp.id,
            'interaction_type', tp.interaction_type,
            'purpose', tp.purpose,
            'client_name', c.name,
            'lead_name', l.name,
            'location', tp.location,
            'scheduled_date', tp.scheduled_date,
            'scheduled_time', tp.scheduled_time,
            'status', tp.status,
            'completed_at', tp.completed_at
          ) as tp_row,
          COALESCE(tp.scheduled_time, '23:59'::TIME) as time_order
        FROM touchpoints tp
        LEFT JOIN clients c ON tp.client_id = c.id
        LEFT JOIN leads l ON tp.lead_id = l.id
        WHERE tp.user_id = p_user_id 
          AND tp.scheduled_date = p_date
      ) tp
    ), '[]'::JSON),

    'leads', COALESCE((
      SELECT JSON_AGG(lead_row ORDER BY time_order)
      FROM (
        SELECT 
          JSON_BUILD_OBJECT(
            'id', l.id,
            'name', l.name,
            'phone', l.phone,
            'source', l.source,
            'status', l.status,
            'scheduled_time', l.scheduled_time,
            'notes', l.notes
          ) as lead_row,
          COALESCE(l.scheduled_time, '23:59'::TIME) as time_order
        FROM leads l
        WHERE l.user_id = p_user_id 
          AND l.scheduled_date = p_date 
          AND l.status != 'cancelled'
      ) l
    ), '[]'::JSON),

    'business_opportunities', COALESCE((
      SELECT JSON_AGG(bo_row ORDER BY amount_order DESC NULLS LAST)
      FROM (
        SELECT 
          JSON_BUILD_OBJECT(
            'id', bo.id,
            'client_name', c.name,
            'lead_name', l.name,
            'expected_amount', bo.expected_amount,
            'opportunity_stage', bo.opportunity_stage,
            'opportunity_type', bo.opportunity_type,
            'additional_info', bo.additional_info,
            'due_time', bo.due_time,
            'outcome', bo.outcome
          ) as bo_row,
          bo.expected_amount as amount_order
        FROM business_opportunities bo
        LEFT JOIN clients c ON bo.client_id = c.id
        LEFT JOIN leads l ON bo.lead_id = l.id
        WHERE bo.user_id = p_user_id 
          AND bo.due_date = p_date
      ) bo
    ), '[]'::JSON)
  );
$$;

-- ============================================================================
-- PART 6: Queue Management Functions
-- ============================================================================

-- Queue an email job
CREATE OR REPLACE FUNCTION public.queue_email_job(
  p_user_id UUID,
  p_email_type VARCHAR,
  p_target_date DATE,
  p_user_email VARCHAR,
  p_user_name VARCHAR
)
RETURNS BIGINT
LANGUAGE SQL
AS $$
  SELECT pgmq.send(
    'email_jobs',
    JSON_BUILD_OBJECT(
      'user_id', p_user_id,
      'email_type', p_email_type,
      'target_date', p_target_date,
      'user_email', p_user_email,
      'user_name', p_user_name,
      'queued_at', NOW()::TEXT
    )::TEXT
  );
$$;

-- Read from queue with proper return types
CREATE OR REPLACE FUNCTION public.pgmq_read(
  queue_name TEXT,
  vt INTEGER,
  qty INTEGER
)
RETURNS TABLE (
  msg_id bigint,
  read_ct integer,
  enqueued_at timestamptz,
  vt timestamptz,
  message jsonb
)
LANGUAGE PLPGSQL
AS $$
BEGIN
  RETURN QUERY
  SELECT
    m.msg_id,
    m.read_ct,
    m.enqueued_at,
    m.vt,
    m.message
  FROM pgmq.read(queue_name, vt, qty) m;
END;
$$;

-- Delete message from queue
CREATE OR REPLACE FUNCTION public.pgmq_delete(
  queue_name TEXT,
  msg_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE SQL
AS $$
  SELECT pgmq.delete(queue_name, msg_id);
$$;

-- Move message to DLQ
CREATE OR REPLACE FUNCTION public.move_to_dlq(
  p_msg_id BIGINT,
  p_message JSONB,
  p_error TEXT
)
RETURNS VOID
LANGUAGE SQL
AS $$
  SELECT pgmq.send(
    'email_jobs_dlq',
    JSON_BUILD_OBJECT(
      'original_msg_id', p_msg_id,
      'message', p_message,
      'error', p_error,
      'moved_at', NOW()::TEXT
    )::TEXT
  );
$$;

-- ============================================================================
-- PART 7: Grant Permissions
-- ============================================================================

GRANT EXECUTE ON FUNCTION public.get_ist_time() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_ist_date() TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.time_in_window(TIME, TIME, TIME) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_users_for_morning_email(INTEGER) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_users_for_afternoon_email(INTEGER) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_users_for_eod_email(INTEGER) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.get_email_daily_items(UUID, DATE) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.queue_email_job(UUID, VARCHAR, DATE, VARCHAR, VARCHAR) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.pgmq_read(TEXT, INTEGER, INTEGER) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.pgmq_delete(TEXT, BIGINT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.move_to_dlq(BIGINT, JSONB, TEXT) TO authenticated, service_role;
