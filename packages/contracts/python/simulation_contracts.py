from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SimulationScenarioType = Literal[
    "marketing_budget_change",
    "supplier_payment_deferral",
    "roas_improvement",
    "custom_financial_change",
]


class SimulationRequest(BaseModel):
    simulation_name: str = Field(..., min_length=3)
    scenario_type: SimulationScenarioType

    marketing_budget_change_percent: float | None = None
    marketing_scope: Literal["all", "low_roas_only"] = "all"

    supplier_payment_deferral_days: int | None = None
    supplier_payment_deferral_ratio: float = Field(default=0.50, ge=0, le=1)

    target_roas: float | None = None

    custom_revenue_change: float | None = None
    custom_expense_change: float | None = None

    analysis_cashflow_days: int = Field(default=30, ge=7, le=365)
    analysis_marketing_days: int = Field(default=60, ge=7, le=180)


class SimulationAskRequest(BaseModel):
    question: str = Field(..., min_length=5)
    analysis_cashflow_days: int = Field(default=30, ge=7, le=365)
    analysis_marketing_days: int = Field(default=60, ge=7, le=180)


class RunStructuredSimulationRequest(BaseModel):
    company_id: str
    company_name: str | None = None
    user_id: str | None = None
    simulation: SimulationRequest


class RunNaturalLanguageSimulationRequest(BaseModel):
    company_id: str
    company_name: str | None = None
    user_id: str | None = None
    question: str = Field(..., min_length=5)
    analysis_cashflow_days: int = Field(default=30, ge=7, le=365)
    analysis_marketing_days: int = Field(default=60, ge=7, le=180)


class SimulationProjection(BaseModel):
    predicted_revenue_change: float
    predicted_expense_change: float
    predicted_net_cashflow_change: float
    predicted_risk_change: int
    current_risk_score: int | None = None
    projected_risk_score: int | None = None
    projected_risk_level: str | None = None


class SimulationAgentParseResult(BaseModel):
    simulation_request: SimulationRequest
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)
    clarification_needed: bool = False
    clarification_question: str | None = None


class SimulationResponse(BaseModel):
    id: str
    company_id: str
    company_name: str | None = None

    simulation_name: str
    scenario_type: SimulationScenarioType
    input_params: dict[str, Any]

    base_context: dict[str, Any]
    projection: SimulationProjection

    recommended_action: str
    summary: str
    assumptions: list[str] = Field(default_factory=list)

    agent_explanation: str | None = None
    parser_confidence: float | None = None

    result_json: dict[str, Any]
    created_at: str | None = None


class SimulationListItem(BaseModel):
    id: str
    company_id: str
    simulation_name: str
    scenario_type: str | None = None
    predicted_revenue_change: float | None = None
    predicted_expense_change: float | None = None
    predicted_risk_change: int | None = None
    recommended_action: str | None = None
    summary: str | None = None
    created_at: str | None = None