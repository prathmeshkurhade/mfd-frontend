-- Create trigger function for clients table
CREATE OR REPLACE FUNCTION trigger_clients_sync()
RETURNS TRIGGER AS $$
DECLARE
  payload jsonb;
BEGIN
  payload := jsonb_build_object(
    'operation', TG_OP,
    'table_name', 'clients',
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
DROP TRIGGER IF EXISTS clients_sync_insert_trigger ON clients;
DROP TRIGGER IF EXISTS clients_sync_update_trigger ON clients;
DROP TRIGGER IF EXISTS clients_sync_delete_trigger ON clients;

-- Create triggers for clients table
CREATE TRIGGER clients_sync_insert_trigger
AFTER INSERT ON clients
FOR EACH ROW
EXECUTE FUNCTION trigger_clients_sync();

CREATE TRIGGER clients_sync_update_trigger
AFTER UPDATE ON clients
FOR EACH ROW
EXECUTE FUNCTION trigger_clients_sync();

CREATE TRIGGER clients_sync_delete_trigger
AFTER DELETE ON clients
FOR EACH ROW
EXECUTE FUNCTION trigger_clients_sync();
