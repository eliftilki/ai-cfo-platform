from __future__ import annotations

from supabase import Client, create_client

from app.core.config import settings


settings.validate()

ai_cfo_db: Client = create_client(
    settings.ai_cfo_supabase_url,
    settings.ai_cfo_supabase_service_role_key,
)