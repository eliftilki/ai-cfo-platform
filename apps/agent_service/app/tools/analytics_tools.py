from __future__ import annotations

from langchain_core.tools import tool

from app.analytics.cashflow_metrics import compute_cashflow_metrics
from app.analytics.marketing_metrics import compute_marketing_metrics
from app.analytics.risk_metrics import compute_combined_risk_assessment
@tool
def compute_cashflow_metrics_tool(bank_transactions: list) -> dict:
    """Compute cashflow metrics tool from normalized input data."""
    return compute_cashflow_metrics(bank_transactions)


@tool
def compute_marketing_metrics_tool(campaigns: list) -> dict:
    """Compute marketing metrics tool from normalized input data."""
    return compute_marketing_metrics(campaigns)


@tool
def compute_combined_risk_assessment_tool(
    cashflow_metrics: dict | None,
    marketing_metrics: dict | None,
    latest_risk_score: dict | None,
) -> dict:
    """Compute combined risk assessment tool from normalized input data."""
    return compute_combined_risk_assessment(
        cashflow_metrics=cashflow_metrics,
        marketing_metrics=marketing_metrics,
        latest_risk_score=latest_risk_score,
    )