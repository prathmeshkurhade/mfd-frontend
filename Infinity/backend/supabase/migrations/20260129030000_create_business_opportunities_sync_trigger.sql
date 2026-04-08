-- Create trigger function for business_opportunities table
CREATE OR REPLACE FUNCTION trigger_business_opportunities_sync()
RETURNS TRIGGER AS $$
DECLARE
  payload jsonb;
BEGIN
  payload := jsonb_build_object(
    'operation', TG_OP,
    'table_name', 'business_opportunities',
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
DROP TRIGGER IF EXISTS business_opportunities_sync_insert_trigger ON business_opportunities;
DROP TRIGGER IF EXISTS business_opportunities_sync_update_trigger ON business_opportunities;
DROP TRIGGER IF EXISTS business_opportunities_sync_delete_trigger ON business_opportunities;

-- Create triggers for business_opportunities table
CREATE TRIGGER business_opportunities_sync_insert_trigger
AFTER INSERT ON business_opportunities
FOR EACH ROW
EXECUTE FUNCTION trigger_business_opportunities_sync();

CREATE TRIGGER business_opportunities_sync_update_trigger
AFTER UPDATE ON business_opportunities
FOR EACH ROW
EXECUTE FUNCTION trigger_business_opportunities_sync();

CREATE TRIGGER business_opportunities_sync_delete_trigger
AFTER DELETE ON business_opportunities
FOR EACH ROW
EXECUTE FUNCTION trigger_business_opportunities_sync();
