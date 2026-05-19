from __future__ import annotations

import logging
from copy import deepcopy

from app.agents.output_contracts import build_agent_output_contract, merge_agent_contracts
from app.presentation.risk_label_mappers import map_risk_factor_label_tr, map_risk_label_tr
from app.schemas.agent_outputs import RiskPrioritizationOutput
from app.services.supabase_service import create_agent_run, complete_agent_run, save_agent_output
from app.tools.analytics_tools import compute_combined_risk_assessment_tool
from app.tools.llm_tools import generate_risk_summary_tool


AGENT_NAME = "risk_prioritization_engine"
logger = logging.getLogger(__name__)


def _build_presentation_risk_assessment(risk_assessment: dict) -> dict:
    """Build presentation risk assessment for downstream service or UI use."""
    data = deepcopy(risk_assessment)
    data["overall_risk_level"] = map_risk_label_tr(data.get("overall_risk_level"))
    data["top_risk_factors"] = [
        map_risk_factor_label_tr(x) for x in data.get("top_risk_factors", [])
    ]
    return data


def _fallback_risk_summary(
    company_name: str,
    risk_assessment: dict,
    agent_contracts: dict | None = None,
) -> str:
    """Build a deterministic fallback for risk summary."""
    level = risk_assessment.get("overall_risk_level", "bilinmiyor")
    score = risk_assessment.get("overall_risk_score", 0)
    factors = risk_assessment.get("top_risk_factors", [])
    issue_codes = _domain_contract_issue_codes(agent_contracts)

    confidence_note = ""
    if "data_quality_warning" in issue_codes:
        confidence_note = (
            " Nakit akışı ve pazarlama tarafında veri güveni sınırlı olduğu için "
            "risk seviyesi kesin hüküm olarak okunmamalıdır."
        )
    elif any(code.startswith("cashflow_") for code in issue_codes):
        confidence_note = " Nakit akışı verisi sınırlı olduğu için likidite kaynaklı risk yorumu temkinli değerlendirilmelidir."
    elif any(code.startswith("marketing_") for code in issue_codes):
        confidence_note = " Pazarlama tarafında veri sınırlı olduğu için ticari verimlilik kaynaklı risk yorumu temkinli değerlendirilmelidir."

    factor_text = "Belirgin risk faktörü sınırlı görünüyor."
    if factors:
        factor_text = "Öne çıkan risk faktörleri: " + ", ".join(factors[:3]) + "."

    actions = risk_assessment.get("priority_actions", [])
    default_actions = [
        "Bugün en yüksek risk yaratan nakit çıkışı veya kampanya alanını belirleyip yönetim gündemine alın.",
        "Bu hafta nakit akışı ve pazarlama verimliliğini aynı risk görünümünde izleyin.",
        "Veri kapsamı sınırlıysa karar öncesi eksik alanları tamamlayıp risk skorunu yeniden çalıştırın.",
    ]
    final_actions = (actions + default_actions)[:3]

    return "\n".join(
        [
            f"Risk özeti: {company_name} için kısa vadeli risk seviyesi {level}; risk skoru {score} olarak izleniyor.{confidence_note}",
            "",
            "Bulgular:",
            f"- {factor_text}",
            "- Bu değerlendirme, mevcut nakit akışı ve pazarlama sinyallerinin birlikte okunmasına dayanır.",
            "",
            "Risk azaltıcı aksiyonlar:",
            f"1. {final_actions[0]}",
            f"2. {final_actions[1]}",
            f"3. {final_actions[2]}",
        ]
    )


def _domain_contract_issue_codes(agent_contracts: dict | None) -> list[str]:
    """Build risk-layer issue codes from upstream domain contracts."""
    contracts = agent_contracts or {}
    issue_codes: list[str] = []
    low_confidence_domains: list[str] = []

    domain_map = {
        "cashflow_agent": "cashflow",
        "marketing_agent": "marketing",
    }

    for agent_name, domain_name in domain_map.items():
        contract = contracts.get(agent_name)
        if not isinstance(contract, dict):
            continue

        confidence = contract.get("confidence")
        try:
            confidence_value = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence_value = None

        if confidence_value is not None and confidence_value < 0.70:
            issue_codes.append(f"{domain_name}_low_confidence")
            low_confidence_domains.append(domain_name)

        for error in contract.get("errors", []):
            issue_codes.append(f"{domain_name}_{error}")

        data_coverage = contract.get("data_coverage") or {}
        if data_coverage.get("data_coverage_note") and (
            data_coverage.get("actual_period_days") is not None
            and data_coverage.get("effective_period_days") is not None
            and data_coverage.get("actual_period_days") < data_coverage.get("effective_period_days")
        ):
            issue_codes.append(f"{domain_name}_limited_data_coverage")

    if len(set(low_confidence_domains)) >= 2:
        issue_codes.append("data_quality_warning")

    return sorted(set(issue_codes))


def risk_prioritization_engine_node(state: dict) -> dict:
    """Risk prioritization engine node for the service workflow."""
    company_id = state["company_id"]
    company_name = state.get("company_name") or company_id
    user_question = state["user_question"]
    analysis_mode = state.get("analysis_mode", "synthesis_risk")

    cashflow_metrics = state.get("cashflow_metrics")
    marketing_metrics = state.get("marketing_metrics")
    agent_contracts = state.get("agent_contracts") or {}

    agent_run_id = None

    try:
        agent_run = create_agent_run(
            company_id=company_id,
            agent_name=AGENT_NAME,
            trigger_type=state.get("trigger_type", "user_query"),
            trigger_reference=state.get("trigger_reference"),
            run_group_id=state.get("run_group_id"),
            status="running",
        )
        agent_run_id = agent_run["id"]
    except Exception as exc:
        logger.warning("Could not create risk prioritization run: %s", exc)

    try:
        raw_risk_assessment = compute_combined_risk_assessment_tool.invoke(
            {
                "cashflow_metrics": cashflow_metrics,
                "marketing_metrics": marketing_metrics,
                "latest_risk_score": None,
            }
        )
        presentation_risk_assessment = _build_presentation_risk_assessment(raw_risk_assessment)

        summary: str | None = None
        if analysis_mode == "synthesis_risk":
            fallback_summary = _fallback_risk_summary(
                company_name=company_name,
                risk_assessment=presentation_risk_assessment,
                agent_contracts=agent_contracts,
            )

            try:
                summary = generate_risk_summary_tool.invoke(
                    {
                        "company_name": company_name,
                        "risk_assessment": presentation_risk_assessment,
                        "cashflow_metrics": state.get("cashflow_metrics_presentation", cashflow_metrics),
                        "marketing_metrics": state.get("marketing_metrics_presentation", marketing_metrics),
                        "latest_risk_score": None,
                        "user_question": user_question,
                        "agent_contracts": agent_contracts,
                    }
                )
            except Exception as exc:
                logger.warning("Risk prioritization LLM summary failed: %s. Falling back.", exc)
                summary = fallback_summary

        missing_inputs = []
        if not cashflow_metrics:
            missing_inputs.append("cashflow_metrics_missing")
        if not marketing_metrics:
            missing_inputs.append("marketing_metrics_missing")

        missing_inputs.extend(_domain_contract_issue_codes(agent_contracts))
        missing_inputs = sorted(set(missing_inputs))

        confidence = 0.90
        if len(missing_inputs) == 1:
            confidence = 0.65
        elif len(missing_inputs) >= 2:
            confidence = 0.45

        contract = build_agent_output_contract(
            agent_name=AGENT_NAME,
            metrics=raw_risk_assessment,
            flags=sorted(set(raw_risk_assessment.get("top_risk_factors", []) + missing_inputs)),
            summary=summary,
            confidence=confidence,
            data_coverage={
                "cashflow": state.get("cashflow_period_context"),
                "marketing": state.get("marketing_period_context"),
            },
            errors=missing_inputs,
        )

        output = RiskPrioritizationOutput(
            contract=contract,
            risk_assessment=raw_risk_assessment,
            top_risk_factors=raw_risk_assessment.get("top_risk_factors", []),
            priority_actions=raw_risk_assessment.get("priority_actions", []),
            risk_summary=summary,
        )

        persist_ok = True
        if agent_run_id:
            try:
                save_agent_output(
                    company_id=company_id,
                    agent_run_id=agent_run_id,
                    agent_name=AGENT_NAME,
                    output_type="risk_prioritization",
                    summary=summary or "Risk değerlendirmesi ve öncelikli aksiyonlar üretildi.",
                    output_json={
                        "contract": output.dict(),
                        "standard_contract": contract.dict(),
                        "presentation_risk_assessment": presentation_risk_assessment,
                    },
                    confidence_score=0.90,
                )
            except Exception as exc:
                persist_ok = False
                logger.warning("Could not persist risk prioritization output: %s", exc)

            try:
                complete_agent_run(agent_run_id, status="completed" if persist_ok else "failed")
            except Exception as exc:
                logger.warning("Could not finalize risk prioritization run: %s", exc)

        return {
            **state,
            "risk_output": output.dict(),
            "risk_assessment": raw_risk_assessment,
            "risk_assessment_presentation": presentation_risk_assessment,
            "top_risk_factors": output.top_risk_factors,
            "priority_actions": output.priority_actions,
            "risk_summary": summary,
            "risk_contract": contract.dict(),
            "agent_contracts": merge_agent_contracts(state, contract),
            "agent_run_id": agent_run_id,
        }

    except Exception:
        if agent_run_id:
            try:
                complete_agent_run(agent_run_id, status="failed")
            except Exception as exc:
                logger.warning("Could not mark risk prioritization run as failed: %s", exc)
        raise
