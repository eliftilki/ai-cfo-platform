from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.repositories.supabase_admin import get_supabase_admin


UTC = timezone.utc


def _iso_days_ago(days: int) -> str:
    """Return the ISO timestamp for a day offset in the past."""
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


def _now_iso() -> str:
    """Return the current UTC timestamp as an ISO string."""
    return datetime.now(UTC).isoformat()


def _fetch_all(
    table_name: str,
    filters: list[tuple[str, str, Any]] | None = None,
    order_by: str | None = None,
    order_desc: bool = False,
    page_size: int = 1000,
) -> list[dict]:
    """Fetch all matching Supabase rows with pagination."""
    supabase = get_supabase_admin()
    rows: list[dict] = []
    start = 0

    while True:
        query = supabase.table(table_name).select("*").range(start, start + page_size - 1)

        if filters:
            for op, column, value in filters:
                if op == "eq":
                    query = query.eq(column, value)
                elif op == "gte":
                    query = query.gte(column, value)
                elif op == "lte":
                    query = query.lte(column, value)
                else:
                    raise ValueError(f"Unsupported filter op: {op}")

        if order_by:
            query = query.order(order_by, desc=order_desc)

        response = query.execute()
        data = response.data or []
        rows.extend(data)

        if len(data) < page_size:
            break

        start += page_size

    return rows


def get_latest_dashboard_snapshot(company_id: str, snapshot_type: str = "overview") -> dict | None:
    """Return latest dashboard snapshot."""
    supabase = get_supabase_admin()
    response = (
        supabase.table("dashboard_snapshot_latest")
        .select("*")
        .eq("company_id", company_id)
        .eq("snapshot_type", snapshot_type)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def upsert_latest_dashboard_snapshot(
    *,
    company_id: str,
    snapshot_json: dict,
    cashflow_data_last_seen_at: str | None,
    marketing_data_last_seen_at: str | None,
    risk_score_last_seen_at: str | None,
    alerts_last_seen_at: str | None,
    cashflow_refreshed_at: str | None,
    marketing_refreshed_at: str | None,
    risk_refreshed_at: str | None,
    alerts_refreshed_at: str | None,
    expires_at: str | None,
    is_stale: bool = False,
    snapshot_type: str = "overview",
) -> dict:
    """Upsert latest dashboard snapshot in the backing data store."""
    supabase = get_supabase_admin()
    payload = {
        "company_id": company_id,
        "snapshot_type": snapshot_type,
        "snapshot_json": snapshot_json,
        "cashflow_data_last_seen_at": cashflow_data_last_seen_at,
        "marketing_data_last_seen_at": marketing_data_last_seen_at,
        "risk_score_last_seen_at": risk_score_last_seen_at,
        "alerts_last_seen_at": alerts_last_seen_at,
        "cashflow_refreshed_at": cashflow_refreshed_at,
        "marketing_refreshed_at": marketing_refreshed_at,
        "risk_refreshed_at": risk_refreshed_at,
        "alerts_refreshed_at": alerts_refreshed_at,
        "generated_at": _now_iso(),
        "expires_at": expires_at,
        "is_stale": is_stale,
    }

    response = (
        supabase.table("dashboard_snapshot_latest")
        .upsert(payload, on_conflict="company_id,snapshot_type")
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else payload


def insert_dashboard_snapshot_history(
    *,
    company_id: str,
    snapshot_json: dict,
    cashflow_data_last_seen_at: str | None,
    marketing_data_last_seen_at: str | None,
    risk_score_last_seen_at: str | None,
    alerts_last_seen_at: str | None,
    snapshot_type: str = "overview",
) -> None:
    """Insert dashboard snapshot history into the backing data store."""
    supabase = get_supabase_admin()
    supabase.table("dashboard_snapshot_history").insert(
        {
            "company_id": company_id,
            "snapshot_type": snapshot_type,
            "snapshot_json": snapshot_json,
            "cashflow_data_last_seen_at": cashflow_data_last_seen_at,
            "marketing_data_last_seen_at": marketing_data_last_seen_at,
            "risk_score_last_seen_at": risk_score_last_seen_at,
            "alerts_last_seen_at": alerts_last_seen_at,
            "generated_at": _now_iso(),
        }
    ).execute()


def get_or_create_refresh_state(company_id: str) -> dict:
    """Return or create refresh state."""
    supabase = get_supabase_admin()
    response = (
        supabase.table("dashboard_refresh_state")
        .select("*")
        .eq("company_id", company_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if rows:
        return rows[0]

    payload = {"company_id": company_id}
    created = supabase.table("dashboard_refresh_state").insert(payload).execute()
    return (created.data or [payload])[0]


def update_refresh_state(company_id: str, updates: dict) -> None:
    """Update refresh state in the backing data store."""
    supabase = get_supabase_admin()
    updates = {**updates, "updated_at": _now_iso()}
    supabase.table("dashboard_refresh_state").update(updates).eq("company_id", company_id).execute()


def list_refresh_states() -> list[dict]:
    """List refresh states for the requested company or context."""
    supabase = get_supabase_admin()
    response = supabase.table("dashboard_refresh_state").select("*").execute()
    return response.data or []


def list_company_ids_from_data() -> list[str]:
    """List company ids from data for the requested company or context."""
    supabase = get_supabase_admin()
    company_ids: set[str] = set()

    for table_name in ["bank_transactions", "marketing_campaigns", "risk_scores", "alerts"]:
        response = supabase.table(table_name).select("company_id").limit(5000).execute()
        for row in response.data or []:
            if row.get("company_id"):
                company_ids.add(row["company_id"])

    return sorted(company_ids)


def fetch_company(company_id: str) -> dict | None:
    """Fetch company from the backing data store."""
    supabase = get_supabase_admin()
    response = supabase.table("companies").select("*").eq("id", company_id).limit(1).execute()
    rows = response.data or []
    return rows[0] if rows else None


def fetch_bank_transactions(company_id: str, days: int = 30) -> list[dict]:
    """Fetch bank transactions from the backing data store."""
    return _fetch_all(
        "bank_transactions",
        filters=[
            ("eq", "company_id", company_id),
            ("gte", "transaction_date", _iso_days_ago(days)),
        ],
        order_by="transaction_date",
        order_desc=True,
    )


def fetch_marketing_campaigns(company_id: str, days: int = 60) -> list[dict]:
    """Fetch marketing campaigns from the backing data store."""
    return _fetch_all(
        "marketing_campaigns",
        filters=[
            ("eq", "company_id", company_id),
            ("gte", "campaign_start_at", _iso_days_ago(days)),
        ],
        order_by="campaign_start_at",
        order_desc=True,
    )


def fetch_latest_risk_score(company_id: str) -> dict | None:
    """Fetch latest risk score from the backing data store."""
    supabase = get_supabase_admin()
    response = (
        supabase.table("risk_scores")
        .select("*")
        .eq("company_id", company_id)
        .order("score_date", desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def fetch_alerts(company_id: str, limit: int = 10) -> list[dict]:
    """Fetch alerts from the backing data store."""
    supabase = get_supabase_admin()
    response = (
        supabase.table("alerts")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def get_last_seen_at(company_id: str, table_name: str, date_column: str) -> str | None:
    """Return last seen at."""
    supabase = get_supabase_admin()
    response = (
        supabase.table(table_name)
        .select(date_column)
        .eq("company_id", company_id)
        .order(date_column, desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0].get(date_column) if rows else None