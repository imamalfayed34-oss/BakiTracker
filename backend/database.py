"""
Supabase client.
We expose a single client instance the rest of the app imports.

Two keys exist:
- anon key:    safe for client-side, respects Row Level Security (RLS)
- service key: server-side ONLY, bypasses RLS — use sparingly (admin tasks)

For Phase 0 we only need a connection to prove the pipeline works.
"""
from supabase import create_client, Client
from config import settings

_client: Client | None = None


def get_supabase() -> Client | None:
    """Return a cached Supabase client, or None if not configured yet."""
    global _client
    if _client is not None:
        return _client
    if not settings.supabase_url or not settings.supabase_anon_key:
        return None
    _client = create_client(settings.supabase_url, settings.supabase_anon_key)
    return _client
