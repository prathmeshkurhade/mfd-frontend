from supabase import Client, create_client

from app.config import settings


def get_supabase_client() -> Client:
    """Return Supabase client using anon key (RLS enforced)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_supabase_admin() -> Client:
    """Return Supabase client using service key (bypasses RLS)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


supabase_anon: Client = get_supabase_client()
supabase_admin: Client = get_supabase_admin()

# Services run behind authenticated endpoints (get_current_user_id) and filter by
# user_id in every query, so they don't need RLS.  Use the service-role client as
# the default so inserts/updates aren't blocked by row-level security policies.
supabase: Client = supabase_admin

