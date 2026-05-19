from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentOutputContract(BaseModel):
    agent_name: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)
    summary: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    data_coverage: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class CashflowAgentOutput(BaseModel):
    contract: AgentOutputContract
    cashflow_metrics: dict[str, Any]
    cashflow_flags: list[str] = Field(default_factory=list)
    cashflow_summary: str | None = None
    latest_cashflow_snapshot: dict[str, Any] | None = None


class MarketingAgentOutput(BaseModel):
    contract: AgentOutputContract
    marketing_metrics: dict[str, Any]
    marketing_flags: list[str] = Field(default_factory=list)
    marketing_summary: str | None = None


class RiskPrioritizationOutput(BaseModel):
    contract: AgentOutputContract
    risk_assessment: dict[str, Any]
    top_risk_factors: list[str] = Field(default_factory=list)
    priority_actions: list[str] = Field(default_factory=list)
    risk_summary: str | None = None


class CFOResponseOutput(BaseModel):
    contract: AgentOutputContract
    cfo_summary: str
    executive_brief: str
    final_recommendations: list[str] = Field(default_factory=list)
