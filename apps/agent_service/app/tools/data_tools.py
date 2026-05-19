from __future__ import annotations

from langchain_core.tools import tool

from app.services.supabase_service import (
    fetch_company_bank_transactions,
    fetch_company_cashflow_snapshots,
    fetch_company_expense_invoices,
    fetch_company_macro_data,
    fetch_company_marketing_campaigns,
    fetch_latest_cashflow_snapshot,
    fetch_latest_risk_score,
)
from app.services.supabase_service import (
    fetch_recent_bank_transactions,
    fetch_recent_marketing_campaigns,
)

@tool
def get_recent_bank_transactions_tool(
    company_id: str,
    days: int = 30,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Return recent bank transactions tool."""
    return fetch_recent_bank_transactions(
        company_id=company_id,
        days=days,
        start_date=start_date,
        end_date=end_date,
    )


@tool
def get_latest_cashflow_snapshot_tool(company_id: str) -> dict | None:
    """Return latest cashflow snapshot tool."""
    return fetch_latest_cashflow_snapshot(company_id=company_id)


@tool
def get_latest_risk_score_tool(company_id: str) -> dict | None:
    """Return latest risk score tool."""
    return fetch_latest_risk_score(company_id=company_id)


@tool
def get_recent_marketing_campaigns_tool(company_id: str, days: int = 60) -> list:
    """Return recent marketing campaigns tool."""
    return fetch_company_marketing_campaigns(company_id=company_id, days=days)


@tool
def get_recent_expense_invoices_tool(company_id: str, days: int = 60) -> list:
    """Return recent expense invoices tool."""
    return fetch_company_expense_invoices(company_id=company_id, days=days)


@tool
def get_recent_macro_data_tool(company_id: str, days: int = 90) -> list:
    """Return recent macro data tool."""
    return fetch_company_macro_data(company_id=company_id, days=days)

@tool
def get_recent_marketing_campaigns_tool(
    company_id: str,
    days: int = 60,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Return recent marketing campaigns tool."""
    return fetch_recent_marketing_campaigns(
        company_id=company_id,
        days=days,
        start_date=start_date,
        end_date=end_date,
    )