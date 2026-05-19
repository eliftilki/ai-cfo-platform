from __future__ import annotations

from app.connectors.ai_cfo_db import ai_cfo_db


def get_latest_cashflow_snapshot(company_id: str) -> dict | None:
    """Return latest cashflow snapshot."""
    response = (
        ai_cfo_db.table("cashflow_snapshots")
        .select("*")
        .eq("company_id", company_id)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def get_latest_risk_score(company_id: str) -> dict | None:
    """Return latest risk score."""
    response = (
        ai_cfo_db.table("risk_scores")
        .select("*")
        .eq("company_id", company_id)
        .order("score_date", desc=True)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def get_recent_agent_outputs(company_id: str, limit: int = 10) -> list[dict]:
    """Return recent agent outputs."""
    response = (
        ai_cfo_db.table("agent_outputs")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []