from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AnalysisType = Literal[
    "domain_cashflow",
    "domain_marketing",
    "synthesis_risk",
    "executive_summary",
    "unknown",
]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="User question for AI CFO")


class AskResponse(BaseModel):
    company_id: str
    company_name: str | None = None
    analysis_type: AnalysisType
    selected_agents: list[str]
    final_response: str
    sections: dict[str, dict[str, Any]]
    agent_run_id: str | None = None


class RunAnalysisRequest(BaseModel):
    company_id: str = Field(..., description="Target company identifier")
    question: str = Field(..., description="User question for AI CFO")
    trigger_type: str = Field(default="user_query")
    trigger_reference: str | None = Field(default=None)
    run_group_id: str | None = Field(default=None)
    company_name: str | None = Field(default=None)


class RunAnalysisResponse(BaseModel):
    company_id: str
    company_name: str | None = None
    analysis_type: AnalysisType
    selected_agents: list[str]
    final_response: str
    sections: dict[str, dict[str, Any]]
    agent_run_id: str | None = None