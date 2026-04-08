-- Migration: Fix Supabase Security Advisor Warnings
-- Date: 2026-03-20
-- Purpose: Set search_path on all functions, move pg_net extension,
--          fix overly permissive RLS policies

-- ============================================================================
-- PART 1: Fix search_path on email service functions (from migration 20260206)
-- ============================================================================

-- Time/Date helpers
CREATE OR REPLACE FUNCTION public.get_ist_time()
RETURNS TIME
LANGUAGE SQL
STABLE
SET search_path = ''
AS $$
  SELECT (NOW() AT TIME ZONE 'Asia/Kolkata')::TIME;
$$;

CREATE OR REPLACE FUNCTION public.get_ist_date()
RETURNS DATE
LANGUAGE SQL
STABLE
SET search_path = ''
AS $$
  SELECT (NOW() AT TIME ZONE 'Asia/Kolkata')::DATE;
$$;

CREATE OR REPLACE FUNCTION public.time_in_window(
  check_time TIME,
  window_start TIME,
  window_end TIME
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SET search_path = ''
AS $$
  SELECT CASE
    WHEN window_start < window_end THEN
      check_time >= window_start AND check_time < window_end
    ELSE
      check_time >= window_start OR check_time < window_end
  END;
$$;

-- User selection functions
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
SET search_path = ''
AS $$
  SELECT
    p.user_id,
    p.google_email,
    p.name
  FROM public.mfd_profiles p
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
SET search_path = ''
AS $$
  SELECT
    p.user_id,
    p.google_email,
    p.name
  FROM public.mfd_profiles p
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
SET search_path = ''
AS $$
  SELECT
    p.user_id,
    p.google_email,
    p.name
  FROM public.mfd_profiles p
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

-- Data fetching function
CREATE OR REPLACE FUNCTION public.get_email_daily_items(
  p_user_id UUID,
  p_date DATE
)
RETURNS JSON
LANGUAGE SQL
STABLE
SET search_path = ''
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
        FROM public.tasks t
        LEFT JOIN public.clients c ON t.client_id = c.id
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
        FROM public.touchpoints tp
        LEFT JOIN public.clients c ON tp.client_id = c.id
        LEFT JOIN public.leads l ON tp.lead_id = l.id
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
        FROM public.leads l
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
        FROM public.business_opportunities bo
        LEFT JOIN public.clients c ON bo.client_id = c.id
        LEFT JOIN public.leads l ON bo.lead_id = l.id
        WHERE bo.user_id = p_user_id
          AND bo.due_date = p_date
      ) bo
    ), '[]'::JSON)
  );
$$;

-- Queue management functions
CREATE OR REPLACE FUNCTION public.queue_email_job(
  p_user_id UUID,
  p_email_type VARCHAR,
  p_target_date DATE,
  p_user_email VARCHAR,
  p_user_name VARCHAR
)
RETURNS BIGINT
LANGUAGE SQL
SET search_path = ''
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
SET search_path = ''
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

CREATE OR REPLACE FUNCTION public.pgmq_delete(
  queue_name TEXT,
  msg_id BIGINT
)
RETURNS BOOLEAN
LANGUAGE SQL
SET search_path = ''
AS $$
  SELECT pgmq.delete(queue_name, msg_id);
$$;

CREATE OR REPLACE FUNCTION public.move_to_dlq(
  p_msg_id BIGINT,
  p_message JSONB,
  p_error TEXT
)
RETURNS VOID
LANGUAGE SQL
SET search_path = ''
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
-- PART 2: Fix search_path on functions created outside migrations
-- These functions exist in Supabase but weren't in local migration files.
-- Using CREATE OR REPLACE so they are safe to run (won't fail if signatures match).
-- ============================================================================

-- update_updated_at_column trigger function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE PLPGSQL
SET search_path = ''
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- update_updated_at trigger function (similar purpose, different name)
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER
LANGUAGE PLPGSQL
SET search_path = ''
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- calculate_age function
CREATE OR REPLACE FUNCTION public.calculate_age(birthdate DATE)
RETURNS INTEGER
LANGUAGE SQL
STABLE
SET search_path = ''
AS $$
  SELECT EXTRACT(YEAR FROM age(CURRENT_DATE, birthdate))::INTEGER;
$$;

-- get_client_tenure function
CREATE OR REPLACE FUNCTION public.get_client_tenure(creation_date DATE)
RETURNS TEXT
LANGUAGE SQL
STABLE
SET search_path = ''
AS $$
  SELECT CASE
    WHEN EXTRACT(YEAR FROM age(CURRENT_DATE, creation_date)) >= 5 THEN '5_plus_years'
    WHEN EXTRACT(YEAR FROM age(CURRENT_DATE, creation_date)) >= 3 THEN '3_to_5_years'
    WHEN EXTRACT(YEAR FROM age(CURRENT_DATE, creation_date)) >= 1 THEN '1_to_3_years'
    ELSE 'less_than_1_year'
  END;
$$;

-- get_age_group function
CREATE OR REPLACE FUNCTION public.get_age_group(age INTEGER)
RETURNS TEXT
LANGUAGE SQL
STABLE
SET search_path = ''
AS $$
  SELECT CASE
    WHEN age < 18 THEN 'under_18'
    WHEN age BETWEEN 18 AND 24 THEN '18_to_24'
    WHEN age BETWEEN 25 AND 35 THEN '25_to_35'
    WHEN age BETWEEN 36 AND 45 THEN '36_to_45'
    WHEN age BETWEEN 46 AND 55 THEN '46_to_55'
    WHEN age BETWEEN 56 AND 65 THEN '56_to_65'
    ELSE '65_plus'
  END;
$$;

-- get_aum_bracket function
CREATE OR REPLACE FUNCTION public.get_aum_bracket(aum DECIMAL)
RETURNS TEXT
LANGUAGE SQL
STABLE
SET search_path = ''
AS $$
  SELECT CASE
    WHEN aum >= 10000000 THEN '1_cr_plus'
    WHEN aum >= 5000000 THEN '50_l_to_1_cr'
    WHEN aum >= 2500000 THEN '25_to_50_l'
    WHEN aum >= 1000000 THEN '10_to_25_l'
    WHEN aum >= 500000 THEN '5_to_10_l'
    WHEN aum >= 250000 THEN '2_5_to_5_l'
    WHEN aum >= 100000 THEN '1_to_2_5_l'
    ELSE 'below_1_l'
  END;
$$;

-- get_sip_bracket function
CREATE OR REPLACE FUNCTION public.get_sip_bracket(sip DECIMAL)
RETURNS TEXT
LANGUAGE SQL
STABLE
SET search_path = ''
AS $$
  SELECT CASE
    WHEN sip >= 100000 THEN '1_l_plus'
    WHEN sip >= 50000 THEN '50k_to_1_l'
    WHEN sip >= 25000 THEN '25k_to_50k'
    WHEN sip >= 10000 THEN '10k_to_25k'
    WHEN sip >= 5000 THEN '5k_to_10k'
    ELSE 'below_5k'
  END;
$$;

-- update_client_calculated_fields trigger function
CREATE OR REPLACE FUNCTION public.update_client_calculated_fields()
RETURNS TRIGGER
LANGUAGE PLPGSQL
SET search_path = ''
AS $$
BEGIN
  IF NEW.date_of_birth IS NOT NULL THEN
    NEW.age = public.calculate_age(NEW.date_of_birth);
    NEW.age_group = public.get_age_group(NEW.age);
  END IF;
  IF NEW.total_aum IS NOT NULL THEN
    NEW.aum_bracket = public.get_aum_bracket(NEW.total_aum);
  END IF;
  IF NEW.total_sip IS NOT NULL THEN
    NEW.sip_bracket = public.get_sip_bracket(NEW.total_sip);
  END IF;
  IF NEW.created_at IS NOT NULL THEN
    NEW.tenure = public.get_client_tenure(NEW.created_at::DATE);
  END IF;
  RETURN NEW;
END;
$$;

-- update_client_product_totals function
CREATE OR REPLACE FUNCTION public.update_client_product_totals()
RETURNS TRIGGER
LANGUAGE PLPGSQL
SET search_path = ''
AS $$
BEGIN
  UPDATE public.clients SET
    total_aum = COALESCE((
      SELECT SUM(current_value) FROM public.client_products
      WHERE client_id = COALESCE(NEW.client_id, OLD.client_id)
    ), 0),
    total_sip = COALESCE((
      SELECT SUM(sip_amount) FROM public.client_products
      WHERE client_id = COALESCE(NEW.client_id, OLD.client_id)
        AND sip_amount IS NOT NULL
    ), 0)
  WHERE id = COALESCE(NEW.client_id, OLD.client_id);
  RETURN NEW;
END;
$$;

-- mark_sync_needed function
CREATE OR REPLACE FUNCTION public.mark_sync_needed()
RETURNS TRIGGER
LANGUAGE PLPGSQL
SET search_path = ''
AS $$
BEGIN
  NEW.sync_status = 'pending';
  RETURN NEW;
END;
$$;

-- queue_calendar_event function
CREATE OR REPLACE FUNCTION public.queue_calendar_event()
RETURNS TRIGGER
LANGUAGE PLPGSQL
SET search_path = ''
AS $$
BEGIN
  PERFORM pg_notify('calendar_event', json_build_object(
    'operation', TG_OP,
    'table', TG_TABLE_NAME,
    'record_id', NEW.id,
    'user_id', NEW.user_id
  )::text);
  RETURN NEW;
END;
$$;

-- ============================================================================
-- PART 3: Move pg_net extension out of public schema
-- ============================================================================

-- Note: Moving extensions requires dropping and recreating.
-- Create the extensions schema if it doesn't exist.
CREATE SCHEMA IF NOT EXISTS extensions;

-- Move pg_net to extensions schema
-- WARNING: This drops and recreates the extension. If you have active pg_net
-- usage, run this during a maintenance window.
ALTER EXTENSION pg_net SET SCHEMA extensions;

-- ============================================================================
-- PART 4: Fix overly permissive RLS policies
-- ============================================================================

-- Fix ocr_inputs: Replace "USING (true)" with proper service_role check
DROP POLICY IF EXISTS "Service role full access on ocr_inputs" ON public.ocr_inputs;
CREATE POLICY "Service role full access on ocr_inputs" ON public.ocr_inputs
  FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Fix voice_inputs: Replace "USING (true)" with proper service_role check
DROP POLICY IF EXISTS "Service role can update voice inputs" ON public.voice_inputs;
CREATE POLICY "Service role can update voice inputs" ON public.voice_inputs
  FOR UPDATE
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');
