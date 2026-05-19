from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.connectors.ai_cfo_db import ai_cfo_db


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
    rows: list[dict] = []
    start = 0

    while True:
        query = ai_cfo_db.table(table_name).select("*").range(start, start + page_size - 1)

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


def fetch_company(company_id: str) -> dict | None:
    """Fetch company from the backing data store."""
    response = (
        ai_cfo_db.table("companies")
        .select("*")
        .eq("id", company_id)
        .limit(1)
        .execute()
    )
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
    response = (
        ai_cfo_db.table("risk_scores")
        .select("*")
        .eq("company_id", company_id)
        .order("score_date", desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None


def insert_simulation(
    *,
    company_id: str,
    created_by_user_id: str | None,
    simulation_name: str,
    scenario_type: str,
    input_params: dict,
    result_json: dict,
    predicted_revenue_change: float,
    predicted_expense_change: float,
    predicted_risk_change: int,
    recommended_action: str,
    summary: str,
) -> dict:
    """Insert simulation into the backing data store."""
    payload = {
        "company_id": company_id,
        "created_by_user_id": created_by_user_id,
        "simulation_name": simulation_name,
        "scenario_type": scenario_type,
        "input_params": input_params,
        "base_context_date": _now_iso(),
        "predicted_revenue_change": predicted_revenue_change,
        "predicted_expense_change": predicted_expense_change,
        "predicted_risk_change": predicted_risk_change,
        "recommended_action": recommended_action,
        "summary": summary,
        "result_json": result_json,
        "status": "completed",
    }

    response = ai_cfo_db.table("simulations").insert(payload).execute()
    rows = response.data or []

    if not rows:
        raise ValueError("Failed to insert simulation.")

    return rows[0]


def list_simulations(company_id: str, limit: int = 20) -> list[dict]:
    """List simulations for the requested company or context."""
    response = (
        ai_cfo_db.table("simulations")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def get_simulation(company_id: str, simulation_id: str) -> dict | None:
    """Return simulation."""
    response = (
        ai_cfo_db.table("simulations")
        .select("*")
        .eq("company_id", company_id)
        .eq("id", simulation_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    return rows[0] if rows else None