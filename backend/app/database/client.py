"""Supabase service-role client. Single instance per process."""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a singleton Supabase client authenticated with the service role key.

    Service role bypasses RLS (see infra/supabase/migrations/001.initial.schema.sql).
    Never expose this client to anything outside the backend.
    """
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key.get_secret_value(),
    )
