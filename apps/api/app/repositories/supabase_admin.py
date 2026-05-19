from __future__ import annotations

from supabase import Client, create_client

from app.core.config import settings


_supabase_admin: Client | None = None


def get_supabase_admin() -> Client:
    """Return supabase admin."""
    global _supabase_admin

    if _supabase_admin is None:
        _supabase_admin = create_client(
            settings.ai_cfo_supabase_url,
            settings.ai_cfo_supabase_service_role_key,
        )

    return _supabase_admin