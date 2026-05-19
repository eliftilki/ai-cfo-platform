from __future__ import annotations

import jwt

from app.core.config import settings


def decode_supabase_jwt(token: str) -> dict:
    """Decode supabase jwt and return its payload."""
    payload = jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        audience="authenticated",
        options={"verify_signature": True},
    )
    return payload