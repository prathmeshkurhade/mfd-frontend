-- Enable pg_net extension if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;

-- Create trigger function for leads table
CREATE OR REPLACE FUNCTION trigger_leads_sync()
RETURNS TRIGGER AS $$
DECLARE
  payload jsonb;
BEGIN
  payload := jsonb_build_object(
    'operation', TG_OP,
    'table_name', 'leads',
    'record', CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD) ELSE row_to_json(NEW) END
  );

  -- Async call to edge function (fire and forget)
  PERFORM
    pg_net.http_post(
      url := 'https://whjgmbptnlsxswehlfhq.supabase.co/functions/v1/push-to-sheets',
      body := payload,
      headers := jsonb_build_object('Content-Type', 'application/json')
    );

  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
EXCEPTION WHEN OTHERS THEN
  -- Silently fail - don't block database operation if edge function call fails
  RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop existing triggers
DROP TRIGGER IF EXISTS leads_sync_insert_trigger ON leads;
DROP TRIGGER IF EXISTS leads_sync_update_trigger ON leads;
DROP TRIGGER IF EXISTS leads_sync_delete_trigger ON leads;

-- Create triggers for leads table
CREATE TRIGGER leads_sync_insert_trigger
AFTER INSERT ON leads
FOR EACH ROW
EXECUTE FUNCTION trigger_leads_sync();

CREATE TRIGGER leads_sync_update_trigger
AFTER UPDATE ON leads
FOR EACH ROW
EXECUTE FUNCTION trigger_leads_sync();

CREATE TRIGGER leads_sync_delete_trigger
AFTER DELETE ON leads
FOR EACH ROW
EXECUTE FUNCTION trigger_leads_sync();
