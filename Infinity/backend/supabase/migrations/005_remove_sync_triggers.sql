-- ============================================================
-- Migration: Remove old push-to-sheets sync triggers
-- Replacing with sync-sheet-snapshot and import-from-sheet
-- ============================================================

-- Drop the 9 sync triggers (exact names from database)
DROP TRIGGER IF EXISTS leads_sync_insert_trigger ON public.leads;
DROP TRIGGER IF EXISTS leads_sync_update_trigger ON public.leads;
DROP TRIGGER IF EXISTS leads_sync_delete_trigger ON public.leads;
DROP TRIGGER IF EXISTS clients_sync_insert_trigger ON public.clients;
DROP TRIGGER IF EXISTS clients_sync_update_trigger ON public.clients;
DROP TRIGGER IF EXISTS clients_sync_delete_trigger ON public.clients;
DROP TRIGGER IF EXISTS business_opportunities_sync_insert_trigger ON public.business_opportunities;
DROP TRIGGER IF EXISTS business_opportunities_sync_update_trigger ON public.business_opportunities;
DROP TRIGGER IF EXISTS business_opportunities_sync_delete_trigger ON public.business_opportunities;

-- Drop the 3 trigger functions
DROP FUNCTION IF EXISTS public.trigger_leads_sync();
DROP FUNCTION IF EXISTS public.trigger_clients_sync();
DROP FUNCTION IF EXISTS public.trigger_business_opportunities_sync();
