from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from app.connectors.ai_cfo_db import ai_cfo_db


UTC = timezone.utc
DEFAULT_LIMIT = 10000


def _iso_days_ago(days: int) -> str:
    """Return the ISO timestamp for a day offset in the past."""
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


def _normalize_date_value(value: str | None) -> str | None:
    """
    Accepts values like:
    - 2026-05-01
    - 2026-05-01T00:00:00+00:00
    - None

    Supabase/Postgres can compare ISO date strings against timestamptz fields.
    """
    if not value:
        return None

    return value.strip()


from datetime import datetime, timezone
from typing import Any


UTC = timezone.utc


def _now_iso() -> str:
    """Return the current UTC timestamp as an ISO string."""
    return datetime.now(UTC).isoformat()


def _build_date_filters(
    *,
    date_column: str,
    days: int,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[tuple[str, str, Any]]:
    """
    If explicit start_date is provided, use it.
    Otherwise, use rolling lookback window based on days.

    Important:
    - If end_date is provided, it caps the upper bound.
    - If end_date is not provided, cap the upper bound at now().
      This prevents future-dated rows from being included in rolling-window analysis.
    """
    filters: list[tuple[str, str, Any]] = []

    normalized_start = _normalize_date_value(start_date)
    normalized_end = _normalize_date_value(end_date)

    if normalized_start:
        filters.append(("gte", date_column, normalized_start))
    else:
        filters.append(("gte", date_column, _iso_days_ago(days)))

    if normalized_end:
        filters.append(("lte", date_column, normalized_end))
    else:
        filters.append(("lte", date_column, _now_iso()))

    return filters


def _fetch_all(
    table_name: str,
    filters: list[tuple[str, str, Any]] | None = None,
    columns: str = "*",
    order_by: str | None = None,
    order_desc: bool = False,
    page_size: int = 1000,
) -> list[dict]:
    """Fetch all matching Supabase rows with pagination."""
    rows: list[dict] = []
    start = 0

    while True:
        query = (
            ai_cfo_db.table(table_name)
            .select(columns)
            .range(start, start + page_size - 1)
        )

        if filters:
            for op, column, value in filters:
                if op == "eq":
                    query = query.eq(column, value)
                elif op == "gte":
                    query = query.gte(column, value)
                elif op == "lte":
                    query = query.lte(column, value)
                elif op == "in":
                    query = query.in_(column, value)
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


# =========================================================
# CASHFLOW / BANK DATA
# =========================================================

def fetch_company_bank_transactions(
    company_id: str,
    days: int = 30,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Fetch company bank transactions from the backing data store."""
    filters: list[tuple[str, str, Any]] = [
        ("eq", "company_id", company_id),
    ]

    filters.extend(
        _build_date_filters(
            date_column="transaction_date",
            days=days,
            start_date=start_date,
            end_date=end_date,
        )
    )

    return _fetch_all(
        "bank_transactions",
        filters=filters,
        order_by="transaction_date",
        order_desc=True,
    )


def fetch_recent_bank_transactions(
    company_id: str,
    days: int = 30,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """
    Compatibility alias for data_tools or older code.
    """
    return fetch_company_bank_transactions(
        company_id=company_id,
        days=days,
        start_date=start_date,
        end_date=end_date,
    )


def fetch_company_cashflow_snapshots(company_id: str, limit: int = 10) -> list[dict]:
    """Fetch company cashflow snapshots from the backing data store."""
    response = (
        ai_cfo_db.table("cashflow_snapshots")
        .select("*")
        .eq("company_id", company_id)
        .order("snapshot_date", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def fetch_latest_cashflow_snapshot(company_id: str) -> dict | None:
    """Fetch latest cashflow snapshot from the backing data store."""
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


# =========================================================
# RISK DATA
# =========================================================

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
    data = response.data or []
    return data[0] if data else None


# =========================================================
# MARKETING DATA
# =========================================================

def fetch_company_marketing_campaigns(
    company_id: str,
    days: int = 60,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Fetch company marketing campaigns from the backing data store."""
    filters: list[tuple[str, str, Any]] = [
        ("eq", "company_id", company_id),
    ]

    filters.extend(
        _build_date_filters(
            date_column="campaign_start_at",
            days=days,
            start_date=start_date,
            end_date=end_date,
        )
    )

    return _fetch_all(
        "marketing_campaigns",
        filters=filters,
        order_by="campaign_start_at",
        order_desc=True,
    )


def fetch_recent_marketing_campaigns(
    company_id: str,
    days: int = 60,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """
    Compatibility alias for data_tools or older code.
    """
    return fetch_company_marketing_campaigns(
        company_id=company_id,
        days=days,
        start_date=start_date,
        end_date=end_date,
    )


# =========================================================
# EXPENSE / MACRO DATA
# =========================================================

def fetch_company_expense_invoices(
    company_id: str,
    days: int = 60,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Fetch company expense invoices from the backing data store."""
    filters: list[tuple[str, str, Any]] = [
        ("eq", "company_id", company_id),
    ]

    filters.extend(
        _build_date_filters(
            date_column="invoice_date",
            days=days,
            start_date=start_date,
            end_date=end_date,
        )
    )

    return _fetch_all(
        "expense_invoices",
        filters=filters,
        order_by="invoice_date",
        order_desc=True,
    )


def fetch_company_macro_data(
    company_id: str,
    days: int = 90,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Fetch company macro data from the backing data store."""
    filters: list[tuple[str, str, Any]] = [
        ("eq", "company_id", company_id),
    ]

    filters.extend(
        _build_date_filters(
            date_column="captured_at",
            days=days,
            start_date=start_date,
            end_date=end_date,
        )
    )

    return _fetch_all(
        "macro_market_data",
        filters=filters,
        order_by="captured_at",
        order_desc=True,
    )


# =========================================================
# AGENT RUNS
# =========================================================

def create_agent_run(
    company_id: str,
    agent_name: str,
    trigger_type: str,
    trigger_reference: str | None = None,
    status: str = "running",
    run_group_id: str | None = None,
) -> dict:
    """Create agent run in the backing data store."""
    payload = {
        "company_id": company_id,
        "run_group_id": run_group_id,
        "agent_name": agent_name,
        "trigger_type": trigger_type,
        "trigger_reference": trigger_reference,
        "status": status,
        "started_at": datetime.now(UTC).isoformat(),
    }

    response = ai_cfo_db.table("agent_runs").insert(payload).execute()
    data = response.data or []

    if not data:
        raise ValueError("Failed to create agent run.")

    return data[0]


def complete_agent_run(agent_run_id: str, status: str = "completed") -> None:
    """Mark agent run as completed in the backing data store."""
    ai_cfo_db.table("agent_runs").update(
        {
            "status": status,
            "ended_at": datetime.now(UTC).isoformat(),
        }
    ).eq("id", agent_run_id).execute()


def save_agent_output(
    company_id: str,
    agent_run_id: str | None,
    agent_name: str,
    output_type: str,
    summary: str,
    output_json: dict,
    confidence_score: float | None = None,
) -> dict:
    """Save agent output for later audit and retrieval."""
    payload = {
        "company_id": company_id,
        "agent_run_id": agent_run_id,
        "agent_name": agent_name,
        "output_type": output_type,
        "summary": summary,
        "output_json": output_json,
        "confidence_score": confidence_score,
    }

    response = ai_cfo_db.table("agent_outputs").insert(payload).execute()
    data = response.data or []

    if not data:
        raise ValueError("Failed to save agent output.")

    return data[0]