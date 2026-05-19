from __future__ import annotations

from fastapi import Header, HTTPException

from app.services.auth_service import AuthError, get_me_from_token


def get_current_user_context(authorization: str | None = Header(default=None)):
    """Return current user context."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Geçerli Bearer token gerekli.")

    token = authorization.replace("Bearer ", "", 1).strip()

    try:
        return get_me_from_token(token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=401, detail="Oturum doğrulanamadı. Lütfen yeniden giriş yapın.")
    
