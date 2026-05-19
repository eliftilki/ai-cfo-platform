from __future__ import annotations

import logging

from app.agents.simulation_agent import (
    generate_simulation_explanation,
    parse_simulation_question,
)
from app.repositories.simulation_repository import (
    fetch_bank_transactions,
    fetch_company,
    fetch_latest_risk_score,
    fetch_marketing_campaigns,
    get_simulation,
    insert_simulation,
    list_simulations,
)
from app.services.simulation_engine import (
    compute_base_cashflow_context,
    compute_base_marketing_context,
    run_deterministic_simulation,
)
from packages.contracts.python.simulation_contracts import (
    SimulationListItem,
    SimulationProjection,
    SimulationRequest,
    SimulationResponse,
)


logger = logging.getLogger(__name__)


def _model_dump(model) -> dict:
    """Serialize a Pydantic model across supported Pydantic versions."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _build_default_assumptions(request: SimulationRequest) -> list[str]:
    """Build default assumptions for downstream service or UI use."""
    if request.scenario_type == "marketing_budget_change":
        return [
            "Bütçe değişikliğinin belirtilen kampanya kapsamına oransal yansıdığı varsayılmıştır.",
            "Gerçek sonuçlar kanal, kampanya kalitesi ve dönüşüm oranlarına göre değişebilir.",
        ]

    if request.scenario_type == "supplier_payment_deferral":
        return [
            "Tedarikçi ödeme ertelemesi simülasyon dönemindeki nakit çıkışını azaltan geçici bir etki olarak modellenmiştir.",
            "Bu simülasyon borcun ortadan kalktığını değil, nakit çıkışının ötelendiğini varsayar.",
        ]

    if request.scenario_type == "roas_improvement":
        return [
            "Reklam harcaması sabit kabul edilmiştir.",
            "Hedef ROAS gerçekleşirse attributed revenue seviyesinin buna göre artacağı varsayılmıştır.",
        ]

    return [
        "Gelir ve gider değişimleri kullanıcı tarafından verilen varsayımlara göre uygulanmıştır.",
    ]


def _execute_simulation(
    *,
    company_id: str,
    company_name: str | None,
    user_id: str | None,
    request: SimulationRequest,
    original_question: str | None = None,
    parser_confidence: float | None = None,
    assumptions: list[str] | None = None,
    generate_explanation: bool = False,
) -> SimulationResponse:
    """Execute simulation for internal workflow use."""
    company = fetch_company(company_id)
    resolved_company_name = company_name or (company.get("name") if company else None)

    bank_transactions = fetch_bank_transactions(
        company_id=company_id,
        days=request.analysis_cashflow_days,
    )

    campaigns = fetch_marketing_campaigns(
        company_id=company_id,
        days=request.analysis_marketing_days,
    )

    latest_risk_score = fetch_latest_risk_score(company_id)

    cashflow_context = compute_base_cashflow_context(bank_transactions)
    marketing_context = compute_base_marketing_context(campaigns)

    base_context = {
        "company_name": resolved_company_name,
        "cashflow_days": request.analysis_cashflow_days,
        "marketing_days": request.analysis_marketing_days,
        "cashflow": cashflow_context,
        "marketing": marketing_context,
        "latest_risk_score": latest_risk_score,
    }

    projection = run_deterministic_simulation(
        request=request,
        cashflow_context=cashflow_context,
        marketing_context=marketing_context,
        latest_risk_score=latest_risk_score,
    )

    final_assumptions = assumptions or _build_default_assumptions(request)

    agent_explanation = None
    if generate_explanation:
        try:
            agent_explanation = generate_simulation_explanation(
                user_question=original_question,
                simulation_request=request,
                base_context=base_context,
                projection=projection,
                assumptions=final_assumptions,
            )
        except Exception as exc:
            logger.warning("Simulation explanation failed: %s", exc)
            agent_explanation = projection["summary"]

    summary = agent_explanation or projection["summary"]

    result_json = {
        "original_question": original_question,
        "base_context": base_context,
        "projection": projection,
        "assumptions": final_assumptions,
        "agent_explanation": agent_explanation,
        "parser_confidence": parser_confidence,
    }

    saved = insert_simulation(
        company_id=company_id,
        created_by_user_id=user_id,
        simulation_name=request.simulation_name,
        scenario_type=request.scenario_type,
        input_params=_model_dump(request),
        result_json=result_json,
        predicted_revenue_change=projection["predicted_revenue_change"],
        predicted_expense_change=projection["predicted_expense_change"],
        predicted_risk_change=projection["predicted_risk_change"],
        recommended_action=projection["recommended_action"],
        summary=summary,
    )

    return SimulationResponse(
        id=saved["id"],
        company_id=company_id,
        company_name=resolved_company_name,
        simulation_name=request.simulation_name,
        scenario_type=request.scenario_type,
        input_params=_model_dump(request),
        base_context=base_context,
        projection=SimulationProjection(
            predicted_revenue_change=projection["predicted_revenue_change"],
            predicted_expense_change=projection["predicted_expense_change"],
            predicted_net_cashflow_change=projection["predicted_net_cashflow_change"],
            predicted_risk_change=projection["predicted_risk_change"],
            current_risk_score=projection["current_risk_score"],
            projected_risk_score=projection["projected_risk_score"],
            projected_risk_level=projection["projected_risk_level"],
        ),
        recommended_action=projection["recommended_action"],
        summary=summary,
        assumptions=final_assumptions,
        agent_explanation=agent_explanation,
        parser_confidence=parser_confidence,
        result_json=result_json,
        created_at=saved.get("created_at"),
    )


def run_structured_simulation(
    *,
    company_id: str,
    company_name: str | None,
    user_id: str | None,
    request: SimulationRequest,
) -> SimulationResponse:
    """Run structured simulation and return the resulting response."""
    return _execute_simulation(
        company_id=company_id,
        company_name=company_name,
        user_id=user_id,
        request=request,
        original_question=None,
        parser_confidence=None,
        assumptions=None,
        generate_explanation=False,
    )


def run_natural_language_simulation(
    *,
    company_id: str,
    company_name: str | None,
    user_id: str | None,
    question: str,
    analysis_cashflow_days: int = 30,
    analysis_marketing_days: int = 60,
) -> SimulationResponse:
    """Run natural language simulation and return the resulting response."""
    parse_result = parse_simulation_question(
        question=question,
        analysis_cashflow_days=analysis_cashflow_days,
        analysis_marketing_days=analysis_marketing_days,
    )

    if parse_result.clarification_needed:
        raise ValueError(parse_result.clarification_question or "Simülasyon için ek bilgi gerekli.")

    return _execute_simulation(
        company_id=company_id,
        company_name=company_name,
        user_id=user_id,
        request=parse_result.simulation_request,
        original_question=question,
        parser_confidence=parse_result.confidence,
        assumptions=parse_result.assumptions,
        generate_explanation=True,
    )


def get_company_simulations(company_id: str, limit: int = 20) -> list[SimulationListItem]:
    """Return company simulations."""
    rows = list_simulations(company_id=company_id, limit=limit)

    return [
        SimulationListItem(
            id=row["id"],
            company_id=row["company_id"],
            simulation_name=row["simulation_name"],
            scenario_type=row.get("scenario_type"),
            predicted_revenue_change=float(row["predicted_revenue_change"]) if row.get("predicted_revenue_change") is not None else None,
            predicted_expense_change=float(row["predicted_expense_change"]) if row.get("predicted_expense_change") is not None else None,
            predicted_risk_change=row.get("predicted_risk_change"),
            recommended_action=row.get("recommended_action"),
            summary=row.get("summary"),
            created_at=row.get("created_at"),
        )
        for row in rows
    ]


def get_company_simulation(company_id: str, simulation_id: str) -> SimulationResponse:
    """Return company simulation."""
    row = get_simulation(company_id=company_id, simulation_id=simulation_id)
    if not row:
        raise ValueError("Simulation not found.")

    result_json = row.get("result_json") or {}
    projection = result_json.get("projection") or {}
    input_params = row.get("input_params") or {}

    return SimulationResponse(
        id=row["id"],
        company_id=row["company_id"],
        company_name=(result_json.get("base_context") or {}).get("company_name"),
        simulation_name=row["simulation_name"],
        scenario_type=row.get("scenario_type") or input_params.get("scenario_type"),
        input_params=input_params,
        base_context=result_json.get("base_context") or {},
        projection=SimulationProjection(
            predicted_revenue_change=float(row.get("predicted_revenue_change") or projection.get("predicted_revenue_change") or 0),
            predicted_expense_change=float(row.get("predicted_expense_change") or projection.get("predicted_expense_change") or 0),
            predicted_net_cashflow_change=float(projection.get("predicted_net_cashflow_change") or 0),
            predicted_risk_change=int(row.get("predicted_risk_change") or projection.get("predicted_risk_change") or 0),
            current_risk_score=projection.get("current_risk_score"),
            projected_risk_score=projection.get("projected_risk_score"),
            projected_risk_level=projection.get("projected_risk_level"),
        ),
        recommended_action=row.get("recommended_action") or projection.get("recommended_action") or "",
        summary=row.get("summary") or projection.get("summary") or "",
        assumptions=result_json.get("assumptions") or [],
        agent_explanation=result_json.get("agent_explanation"),
        parser_confidence=result_json.get("parser_confidence"),
        result_json=result_json,
        created_at=row.get("created_at"),
    )