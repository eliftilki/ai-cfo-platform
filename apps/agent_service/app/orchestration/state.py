from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    company_id: str
    company_name: str | None

    user_question: str
    trigger_type: str
    trigger_reference: str | None
    run_group_id: str | None

    route_decision: str
    intent: str
    required_agents: list[str]
    requires_synthesis: bool
    requires_executive_response: bool
    intent_confidence: float
    intent_reason: str
    analysis_mode: str

    time_context: dict
    requested_period_days: int | None
    requested_period_label: str | None
    requested_period_was_explicit: bool
    requires_comparison: bool
    comparison_period_days: int | None

    bank_transactions: list
    cashflow_output: dict
    cashflow_metrics: dict
    cashflow_metrics_presentation: dict
    cashflow_flags: list[str]
    latest_cashflow_snapshot: dict | None
    latest_risk_score: dict | None
    cashflow_summary: str | None
    cashflow_period_context: dict
    cashflow_agent_run_id: str | None
    cashflow_contract: dict

    marketing_output: dict
    marketing_metrics: dict
    marketing_metrics_presentation: dict
    marketing_flags: list[str]
    marketing_summary: str | None
    marketing_period_context: dict
    marketing_agent_run_id: str | None
    marketing_contract: dict

    risk_output: dict
    risk_assessment: dict
    risk_assessment_presentation: dict
    top_risk_factors: list[str]
    priority_actions: list[str]
    risk_summary: str | None
    risk_contract: dict

    cfo_output: dict
    cfo_summary: str | None
    executive_brief: str | None
    final_recommendations: list[str]
    cfo_contract: dict
    agent_contracts: dict

    agent_run_id: str
