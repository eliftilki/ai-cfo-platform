from __future__ import annotations

from langchain_core.tools import tool

from app.services.gemini_service import (
    generate_cashflow_summary,
    generate_cfo_summary,
    generate_marketing_summary,
    generate_risk_summary,
)


@tool
def generate_cashflow_summary_tool(
    company_name: str,
    metrics: dict,
    latest_snapshot: dict | None,
    latest_risk_score: dict | None,
    user_question: str,
    period_context: dict | None = None,
) -> str:
    """Generate cashflow summary tool for the AI CFO workflow."""
    return generate_cashflow_summary(
        company_name=company_name,
        metrics=metrics,
        latest_snapshot=latest_snapshot,
        latest_risk_score=latest_risk_score,
        user_question=user_question,
        period_context=period_context,
    )


@tool
def generate_marketing_summary_tool(
    company_name: str,
    metrics: dict,
    latest_risk_score: dict | None,
    user_question: str,
    period_context: dict | None = None,
) -> str:
    """Generate marketing summary tool for the AI CFO workflow."""
    return generate_marketing_summary(
        company_name=company_name,
        metrics=metrics,
        latest_risk_score=latest_risk_score,
        user_question=user_question,
        period_context=period_context,
    )


@tool
def generate_risk_summary_tool(
    company_name: str,
    risk_assessment: dict,
    cashflow_metrics: dict | None,
    marketing_metrics: dict | None,
    latest_risk_score: dict | None,
    user_question: str,
    agent_contracts: dict | None = None,
) -> str:
    """Generate risk summary tool for the AI CFO workflow."""
    return generate_risk_summary(
        company_name=company_name,
        risk_assessment=risk_assessment,
        cashflow_metrics=cashflow_metrics,
        marketing_metrics=marketing_metrics,
        latest_risk_score=latest_risk_score,
        user_question=user_question,
        agent_contracts=agent_contracts,
    )


@tool
def generate_cfo_summary_tool(
    company_name: str,
    cashflow_metrics: dict | None,
    marketing_metrics: dict | None,
    risk_assessment: dict | None,
    latest_risk_score: dict | None,
    user_question: str,
    agent_contracts: dict | None = None,
) -> str:
    """Generate the CFO summary through the LLM service."""
    return generate_cfo_summary(
        company_name=company_name,
        cashflow_metrics=cashflow_metrics,
        marketing_metrics=marketing_metrics,
        risk_assessment=risk_assessment,
        latest_risk_score=latest_risk_score,
        user_question=user_question,
        agent_contracts=agent_contracts,
    )
