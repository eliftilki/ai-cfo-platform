from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from packages.contracts.python.analysis_contracts import (
    RunAnalysisRequest,
    RunAnalysisResponse,
)

from app.orchestration.graph import build_analysis_graph


router = APIRouter()
graph = build_analysis_graph()


def _build_response_from_state(
    company_id: str,
    company_name: str | None,
    result: dict,
) -> RunAnalysisResponse:
    """Build response from state for downstream service or UI use."""
    sections: dict[str, dict[str, Any]] = {}
    selected_agents: list[str] = []

    cashflow_metrics = result.get("cashflow_metrics_presentation", result.get("cashflow_metrics"))
    cashflow_summary = result.get("cashflow_summary")
    cashflow_contract = result.get("cashflow_contract") or {}
    if cashflow_metrics:
        selected_agents.append("cashflow_agent")
        sections["cashflow"] = {
            "metrics": cashflow_metrics,
            "flags": result.get("cashflow_flags", []),
            "summary": cashflow_summary,
            "confidence": cashflow_contract.get("confidence"),
            "data_coverage": cashflow_contract.get("data_coverage", result.get("cashflow_period_context")),
            "errors": cashflow_contract.get("errors", []),
            "contract": cashflow_contract,
            "period_context": result.get("cashflow_period_context"),
            "latest_snapshot": result.get("latest_cashflow_snapshot"),
            "latest_risk_score": result.get("latest_risk_score"),
        }

    marketing_metrics = result.get("marketing_metrics_presentation", result.get("marketing_metrics"))
    marketing_summary = result.get("marketing_summary")
    marketing_contract = result.get("marketing_contract") or {}
    if marketing_metrics:
        selected_agents.append("marketing_agent")
        sections["marketing"] = {
            "metrics": marketing_metrics,
            "flags": result.get("marketing_flags", []),
            "summary": marketing_summary,
            "confidence": marketing_contract.get("confidence"),
            "data_coverage": marketing_contract.get("data_coverage", result.get("marketing_period_context")),
            "errors": marketing_contract.get("errors", []),
            "contract": marketing_contract,
            "period_context": result.get("marketing_period_context"),
        }

    risk_assessment = result.get("risk_assessment_presentation", result.get("risk_assessment"))
    risk_summary = result.get("risk_summary")
    risk_contract = result.get("risk_contract") or {}
    if risk_assessment:
        selected_agents.append("risk_prioritization_engine")
        sections["risk"] = {
            "assessment": risk_assessment,
            "metrics": risk_contract.get("metrics", result.get("risk_assessment", {})),
            "flags": risk_contract.get("flags", result.get("top_risk_factors", [])),
            "summary": risk_summary,
            "confidence": risk_contract.get("confidence"),
            "data_coverage": risk_contract.get("data_coverage", {}),
            "errors": risk_contract.get("errors", []),
            "contract": risk_contract,
            "top_risk_factors": result.get("top_risk_factors", []),
            "priority_actions": result.get("priority_actions", []),
        }

    cfo_summary = result.get("cfo_summary")
    final_recommendations = result.get("final_recommendations", [])
    executive_brief = result.get("executive_brief")
    cfo_contract = result.get("cfo_contract") or {}
    if cfo_summary:
        selected_agents.append("cfo_response_generator")
        sections["cfo"] = {
            "metrics": cfo_contract.get("metrics", {}),
            "flags": cfo_contract.get("flags", final_recommendations),
            "summary": cfo_summary,
            "confidence": cfo_contract.get("confidence"),
            "data_coverage": cfo_contract.get("data_coverage", {}),
            "errors": cfo_contract.get("errors", []),
            "contract": cfo_contract,
            "executive_brief": executive_brief,
            "final_recommendations": final_recommendations,
        }

    analysis_mode = result.get("analysis_mode", "unknown")

    if analysis_mode == "executive_summary" and "cfo" in sections:
        analysis_type = "executive_summary"
        final_response = sections["cfo"]["summary"] or ""
    elif analysis_mode == "synthesis_risk" and "risk" in sections:
        analysis_type = "synthesis_risk"
        final_response = sections["risk"]["summary"] or ""
    elif analysis_mode == "domain_marketing" and "marketing" in sections:
        analysis_type = "domain_marketing"
        final_response = sections["marketing"]["summary"] or ""
    elif analysis_mode == "domain_cashflow" and "cashflow" in sections:
        analysis_type = "domain_cashflow"
        final_response = sections["cashflow"]["summary"] or ""
    else:
        analysis_type = "unknown"
        final_response = "Analiz sonucu üretilemedi."

    return RunAnalysisResponse(
        company_id=company_id,
        company_name=company_name,
        analysis_type=analysis_type,
        selected_agents=selected_agents,
        final_response=final_response,
        sections=sections,
        agent_run_id=result.get("agent_run_id"),
    )


@router.post("/run-analysis", response_model=RunAnalysisResponse)
def run_analysis(request: RunAnalysisRequest):
    """Run analysis and return the resulting response."""
    try:
        result = graph.invoke(
            {
                "company_id": request.company_id,
                "company_name": request.company_name,
                "user_question": request.question,
                "trigger_type": request.trigger_type,
                "trigger_reference": request.trigger_reference,
                "run_group_id": request.run_group_id,
            }
        )

        return _build_response_from_state(
            company_id=request.company_id,
            company_name=request.company_name,
            result=result,
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(exc)}")
