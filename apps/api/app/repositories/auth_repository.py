from __future__ import annotations

from uuid import uuid4

from app.repositories.supabase_admin import get_supabase_admin


def get_user_profile(user_id: str) -> dict | None:
    """Return user profile."""
    supabase = get_supabase_admin()
    response = (
        supabase.table("user_profiles")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def get_primary_membership(user_id: str) -> dict | None:
    """Return primary membership."""
    supabase = get_supabase_admin()
    response = (
        supabase.table("user_company_memberships")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .order("is_default", desc=True)
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def get_company_by_id(company_id: str) -> dict | None:
    """Return company by id."""
    supabase = get_supabase_admin()
    response = (
        supabase.table("companies")
        .select("*")
        .eq("id", company_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def create_company(*, name: str) -> dict:
    """Create company for a newly registered user."""
    supabase = get_supabase_admin()
    payload = {
        "id": str(uuid4()),
        "name": name,
    }
    response = supabase.table("companies").insert(payload).execute()
    rows = response.data or []
    return rows[0] if rows else payload


def create_user_profile(*, user_id: str, email: str, full_name: str) -> dict:
    """Create profile row for a Supabase auth user."""
    supabase = get_supabase_admin()
    payload = {
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "is_active": True,
    }
    response = supabase.table("user_profiles").upsert(payload, on_conflict="id").execute()
    rows = response.data or []
    return rows[0] if rows else payload


def create_user_company_membership(*, user_id: str, company_id: str) -> dict:
    """Create default company membership for a user."""
    supabase = get_supabase_admin()
    payload = {
        "user_id": user_id,
        "company_id": company_id,
        "role": "owner",
        "is_default": True,
        "is_active": True,
    }
    response = supabase.table("user_company_memberships").insert(payload).execute()
    rows = response.data or []
    return rows[0] if rows else payload


def insert_login_audit_log(
    *,
    user_id: str | None,
    email: str | None,
    ip_address: str | None,
    user_agent: str | None,
    login_status: str,
) -> None:
    """Insert login audit log into the backing data store."""
    supabase = get_supabase_admin()
    supabase.table("login_audit_logs").insert(
        {
            "user_id": user_id,
            "email": email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "login_status": login_status,
        }
    ).execute()
