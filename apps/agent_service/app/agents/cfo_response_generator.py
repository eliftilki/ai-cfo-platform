from __future__ import annotations

import logging
from copy import deepcopy

from app.agents.output_contracts import build_agent_output_contract, merge_agent_contracts
from app.presentation.cfo_label_mappers import map_risk_label_tr
from app.schemas.agent_outputs import CFOResponseOutput
from app.services.supabase_service import create_agent_run, complete_agent_run, save_agent_output
from app.tools.llm_tools import generate_cfo_summary_tool


AGENT_NAME = "cfo_response_generator"
logger = logging.getLogger(__name__)


def _build_presentation_risk_assessment(risk_assessment: dict | None) -> dict | None:
    """Build presentation risk assessment for downstream service or UI use."""
    if not risk_assessment:
        return None

    data = deepcopy(risk_assessment)
    if "overall_risk_level" in data:
        data["overall_risk_level"] = map_risk_label_tr(data.get("overall_risk_level"))
    return data


def _fallback_final_recommendations(priority_actions: list[str]) -> list[str]:
    """Build a deterministic fallback for final recommendations."""
    if priority_actions:
        return priority_actions[:3]
    return [
        "Bugün: Nakit çıkışlarını durdurma veya erteleme kararı vermeden önce en büyük ödeme kalemlerini öncelik sırasına alın.",
        "Bugün: Düşük verimli pazarlama harcamalarını yeni bütçe artırımlarından önce gözden geçirin.",
        "Bu hafta: Nakit akışı, pazarlama verimliliği ve risk skorunu birlikte izleyen kısa bir yönetim kontrol ritmi kurun.",
    ]


def _fallback_cfo_summary(
    company_name: str,
    cashflow_metrics: dict | None,
    marketing_metrics: dict | None,
    risk_assessment: dict | None,
    final_recommendations: list[str],
    agent_contracts: dict | None = None,
) -> str:
    """Build a deterministic fallback for cfo summary."""
    net_30 = cashflow_metrics.get("net_cashflow_30d") if cashflow_metrics else None
    roas = marketing_metrics.get("overall_roas") if marketing_metrics else None
    risk_level = risk_assessment.get("overall_risk_level", "bilinmiyor") if risk_assessment else "bilinmiyor"
    contracts = agent_contracts or {}
    confidences = [
        float(contract.get("confidence", 0.0))
        for contract in contracts.values()
        if isinstance(contract, dict)
    ]
    min_confidence = min(confidences) if confidences else None
    input_errors = [
        error
        for contract in contracts.values()
        if isinstance(contract, dict)
        for error in contract.get("errors", [])
    ]

    confidence_note = ""
    if min_confidence is not None and min_confidence < 0.70:
        confidence_note = " Değerlendirme, veri güveni sınırlı olduğu için temkinli okunmalıdır."

    error_note = ""
    if input_errors:
        error_note = " Bazı analiz girdileri eksik olduğu için sonuç kesin hüküm olarak değil, yönetim göstergesi olarak ele alınmalıdır."

    findings: list[str] = []
    if net_30 is not None:
        findings.append(f"Nakit tarafında incelenen dönemde net nakit akışı {net_30} seviyesinde görünüyor.")
    else:
        findings.append("Nakit akışı tarafında yeterli bağlam bulunmadığı için likidite yorumu sınırlı tutulmalıdır.")

    if roas is not None:
        findings.append(f"Pazarlama tarafında genel ROAS {roas:.2f}; bütçe kararları bu verimlilik sinyaliyle birlikte değerlendirilmelidir.")
    else:
        findings.append("Pazarlama tarafında veri sınırlı olduğu için kampanya verimliliği kesin şekilde yorumlanmamalıdır.")

    findings.append(f"Birleşik kısa vadeli risk seviyesi {risk_level} olarak izlenmelidir.{confidence_note}{error_note}")

    trimmed_findings = findings[:3]
    action_1 = final_recommendations[0] if len(final_recommendations) > 0 else _fallback_final_recommendations([])[0]
    action_2 = final_recommendations[1] if len(final_recommendations) > 1 else _fallback_final_recommendations([])[1]
    action_3 = final_recommendations[2] if len(final_recommendations) > 2 else _fallback_final_recommendations([])[2]

    return "\n".join(
        [
            f"Yönetici özeti: {company_name} için kısa vadeli görünüm, eldeki veriye göre disiplinli nakit yönetimi ve kontrollü büyüme gerektiriyor.",
            "",
            "Bulgular:",
            *[f"- {finding}" for finding in trimmed_findings],
            "",
            "Öncelikli aksiyonlar:",
            f"1. {action_1}",
            f"2. {action_2}",
            f"3. {action_3}",
        ]
    )


def _derive_cfo_confidence(
    *,
    has_risk_assessment: bool,
    agent_contracts: dict | None,
    input_errors: list[str],
) -> float:
    """Derive CFO confidence from upstream agent contracts."""
    base_confidence = 0.93 if has_risk_assessment else 0.70
    contracts = agent_contracts or {}
    upstream_confidences = [
        float(contract.get("confidence", 0.0))
        for contract in contracts.values()
        if isinstance(contract, dict) and contract.get("confidence") is not None
    ]

    if upstream_confidences:
        base_confidence = min(base_confidence, min(upstream_confidences))

    if input_errors:
        base_confidence = min(base_confidence, 0.65)

    return max(0.0, min(1.0, base_confidence))


def cfo_response_generator_node(state: dict) -> dict:
    """Cfo response generator node for the service workflow."""
    company_id = state["company_id"]
    company_name = state.get("company_name") or company_id
    user_question = state["user_question"]
    analysis_mode = state.get("analysis_mode", "executive_summary")

    if analysis_mode != "executive_summary":
        return state

    cashflow_metrics = state.get("cashflow_metrics_presentation", state.get("cashflow_metrics"))
    marketing_metrics = state.get("marketing_metrics_presentation", state.get("marketing_metrics"))
    risk_assessment = state.get("risk_assessment_presentation", state.get("risk_assessment"))
    priority_actions = state.get("priority_actions", [])

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
        logger.warning("Could not create CFO response run: %s", exc)

    try:
        presentation_risk_assessment = _build_presentation_risk_assessment(risk_assessment)
        final_recommendations = _fallback_final_recommendations(priority_actions)

        fallback_summary = _fallback_cfo_summary(
            company_name=company_name,
            cashflow_metrics=cashflow_metrics,
            marketing_metrics=marketing_metrics,
            risk_assessment=presentation_risk_assessment,
            final_recommendations=final_recommendations,
            agent_contracts=state.get("agent_contracts") or {},
        )

        try:
            summary = generate_cfo_summary_tool.invoke(
                {
                    "company_name": company_name,
                    "cashflow_metrics": cashflow_metrics,
                    "marketing_metrics": marketing_metrics,
                    "risk_assessment": presentation_risk_assessment,
                    "latest_risk_score": None,
                    "user_question": user_question,
                    "agent_contracts": state.get("agent_contracts") or {},
                }
            )
        except Exception as exc:
            logger.warning("CFO response LLM summary failed: %s. Falling back.", exc)
            summary = fallback_summary

        executive_brief = (
            f"{state.get('cashflow_summary', '') or ''} "
            f"{state.get('marketing_summary', '') or ''} "
            f"{state.get('risk_summary', '') or ''}"
        ).strip()

        input_errors = []
        agent_contracts = state.get("agent_contracts") or {}
        for contract in agent_contracts.values():
            if isinstance(contract, dict):
                input_errors.extend(contract.get("errors", []))

        cfo_confidence = _derive_cfo_confidence(
            has_risk_assessment=bool(presentation_risk_assessment),
            agent_contracts=agent_contracts,
            input_errors=input_errors,
        )

        contract = build_agent_output_contract(
            agent_name=AGENT_NAME,
            metrics={
                "recommendation_count": len(final_recommendations),
                "has_cashflow_context": bool(cashflow_metrics),
                "has_marketing_context": bool(marketing_metrics),
                "has_risk_context": bool(presentation_risk_assessment),
            },
            flags=priority_actions,
            summary=summary,
            confidence=cfo_confidence,
            data_coverage={
                "cashflow": state.get("cashflow_period_context"),
                "marketing": state.get("marketing_period_context"),
                "input_agents": list(agent_contracts.keys()),
            },
            errors=input_errors,
        )

        output = CFOResponseOutput(
            contract=contract,
            cfo_summary=summary,
            executive_brief=executive_brief,
            final_recommendations=final_recommendations,
        )

        persist_ok = True
        if agent_run_id:
            try:
                save_agent_output(
                    company_id=company_id,
                    agent_run_id=agent_run_id,
                    agent_name=AGENT_NAME,
                    output_type="cfo_response",
                    summary=summary,
                    output_json={
                        "contract": output.dict(),
                        "standard_contract": contract.dict(),
                    },
                    confidence_score=cfo_confidence,
                )
            except Exception as exc:
                persist_ok = False
                logger.warning("Could not persist CFO response output: %s", exc)

            try:
                complete_agent_run(agent_run_id, status="completed" if persist_ok else "failed")
            except Exception as exc:
                logger.warning("Could not finalize CFO response run: %s", exc)

        return {
            **state,
            "cfo_output": output.dict(),
            "cfo_summary": summary,
            "executive_brief": executive_brief,
            "final_recommendations": final_recommendations,
            "cfo_contract": contract.dict(),
            "agent_contracts": merge_agent_contracts(state, contract),
            "agent_run_id": agent_run_id,
        }

    except Exception:
        if agent_run_id:
            try:
                complete_agent_run(agent_run_id, status="failed")
            except Exception as exc:
                logger.warning("Could not mark CFO response run as failed: %s", exc)
        raise
