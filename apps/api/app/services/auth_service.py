from __future__ import annotations

import httpx

from app.core.config import settings
from app.repositories.auth_repository import (
    create_company,
    create_user_company_membership,
    create_user_profile,
    get_company_by_id,
    get_primary_membership,
    get_user_profile,
    insert_login_audit_log,
)
from packages.contracts.python.auth_contracts import LoginResponse, MeResponse, SignupResponse


class AuthError(Exception):
    pass


def _extract_supabase_error(response: httpx.Response) -> str:
    """Return a user-safe message from a Supabase auth error response."""
    try:
        payload = response.json()
    except ValueError:
        return response.text

    for key in ("msg", "message", "error_description", "error"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    return "Supabase auth request failed."


def _get_supabase_user_from_token(token: str) -> dict:
    """Return supabase user from token."""
    url = f"{settings.resolved_supabase_auth_base_url}/user"
    headers = {
        "apikey": settings.ai_cfo_supabase_service_role_key,
        "Authorization": f"Bearer {token}",
    }

    try:
        response = httpx.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        raise AuthError("Oturum doğrulanamadı. Lütfen yeniden giriş yapın.") from exc

    user_id = data.get("id")
    if not user_id:
        raise AuthError("Oturum bilgisi kullanıcı hesabıyla eşleştirilemedi.")

    return data


def login_user(
    *,
    email: str,
    password: str,
    ip_address: str | None,
    user_agent: str | None,
) -> LoginResponse:
    """Authenticate the user and return session context."""
    url = f"{settings.ai_cfo_supabase_url}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": settings.ai_cfo_supabase_service_role_key,
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "password": password,
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        insert_login_audit_log(
            user_id=None,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            login_status="failed",
        )
        raise AuthError("Giriş başarısız. E-posta veya şifre hatalı olabilir.") from exc

    access_token = data["access_token"]
    refresh_token = data.get("refresh_token")
    expires_in = data.get("expires_in")

    auth_user = _get_supabase_user_from_token(access_token)
    user_id = auth_user["id"]

    profile = get_user_profile(user_id)
    if not profile or not profile.get("is_active", True):
        raise AuthError("Kullanıcı profili aktif değil veya bulunamadı.")

    membership = get_primary_membership(user_id)
    if not membership:
        raise AuthError("Bu kullanıcı için aktif bir şirket eşleşmesi bulunamadı.")

    company_id = membership["company_id"]
    company = get_company_by_id(company_id)

    insert_login_audit_log(
        user_id=user_id,
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        login_status="success",
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user_id=user_id,
        email=email,
        company_id=company_id,
        company_name=company.get("name") if company else None,
    )


def signup_user(
    *,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    company_name: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> SignupResponse:
    """Create a Supabase auth user and application membership."""
    clean_first_name = first_name.strip()
    clean_last_name = last_name.strip()
    clean_email = email.strip().lower()
    full_name = " ".join(part for part in [clean_first_name, clean_last_name] if part)
    resolved_company_name = (company_name or f"{full_name} Workspace").strip()

    if not full_name:
        raise AuthError("Ad ve soyad zorunludur.")
    if len(password) < 6:
        raise AuthError("Sifre en az 6 karakter olmalidir.")

    url = f"{settings.resolved_supabase_auth_base_url}/admin/users"
    headers = {
        "apikey": settings.ai_cfo_supabase_service_role_key,
        "Authorization": f"Bearer {settings.ai_cfo_supabase_service_role_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": clean_email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {
            "first_name": clean_first_name,
            "last_name": clean_last_name,
            "full_name": full_name,
        },
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    except Exception as exc:
        raise AuthError("Supabase baglantisi kurulamadi. Lutfen daha sonra tekrar deneyin.") from exc

    if response.status_code == 422:
        raise AuthError("Bu e-posta adresiyle zaten bir hesap var.")

    if response.status_code >= 400:
        detail = _extract_supabase_error(response)
        raise AuthError(f"Kullanici olusturulamadi: {detail}")

    auth_user = response.json()
    user_id = auth_user.get("id")
    if not user_id:
        raise AuthError("Supabase kullanici kimligi donmedi.")

    try:
        company = create_company(name=resolved_company_name)
        create_user_profile(user_id=user_id, email=clean_email, full_name=full_name)
        create_user_company_membership(user_id=user_id, company_id=company["id"])
    except Exception as exc:
        raise AuthError("Hesap olustu ancak uygulama profili hazirlanamadi.") from exc

    login_response = login_user(
        email=clean_email,
        password=password,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if hasattr(login_response, "model_dump"):
        return SignupResponse(**login_response.model_dump())

    return SignupResponse(**login_response.dict())


def get_me_from_token(token: str) -> MeResponse:
    """Return me from token."""
    auth_user = _get_supabase_user_from_token(token)
    user_id = auth_user["id"]

    profile = get_user_profile(user_id)
    if not profile or not profile.get("is_active", True):
        raise AuthError("Kullanıcı profili aktif değil veya bulunamadı.")

    membership = get_primary_membership(user_id)
    if not membership:
        raise AuthError("Aktif şirket eşleşmesi bulunamadı.")

    company_id = membership["company_id"]
    company = get_company_by_id(company_id)

    return MeResponse(
        user_id=user_id,
        email=profile["email"],
        full_name=profile.get("full_name"),
        company_id=company_id,
        company_name=company.get("name") if company else None,
        role=membership.get("role"),
    )
