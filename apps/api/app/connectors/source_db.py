from __future__ import annotations

from supabase import Client, create_client

from app.core.config import settings


settings.validate()

source_db: Client = create_client(
    settings.source_supabase_url,
    settings.source_supabase_service_role_key,
)