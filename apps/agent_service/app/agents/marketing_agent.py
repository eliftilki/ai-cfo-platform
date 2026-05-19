from __future__ import annotations

import logging
from copy import deepcopy

from app.analytics.risk_prioritization import build_marketing_flags
from app.agents.output_contracts import agent_confidence, build_agent_output_contract, merge_agent_contracts
from app.presentation.marketing_label_mappers import map_platform_label_tr, map_risk_label_tr
from app.schemas.agent_outputs import MarketingAgentOutput
from app.services.supabase_service import create_agent_run, complete_agent_run, save_agent_output
from app.tools.analytics_tools import compute_marketing_metrics_tool
from app.tools.data_tools import get_recent_marketing_campaigns_tool
from app.tools.llm_tools import generate_marketing_summary_tool
from app.orchestration.data_coverage import build_data_coverage_context
from app.orchestration.time_context import resolve_agent_period

AGENT_NAME = "marketing_agent"
logger = logging.getLogger(__name__)


def _format_money(value) -> str:
    """Format a numeric value for Turkish business-facing summaries."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{number:,.0f} TL".replace(",", ".")


def _format_ratio(value) -> str:
    """Format a ratio for Turkish business-facing summaries."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{number:.2f}".replace(".", ",")


def _build_presentation_metrics(metrics: dict) -> dict:
    """Build presentation metrics for downstream service or UI use."""
    presentation_metrics = deepcopy(metrics)
    presentation_metrics["marketing_risk"] = map_risk_label_tr(
        presentation_metrics.get("marketing_risk")
    )

    for item in presentation_metrics.get("platform_summary", []):
        item["platform"] = map_platform_label_tr(item.get("platform"))

    for item in presentation_metrics.get("low_roas_campaigns", []):
        item["platform"] = map_platform_label_tr(item.get("platform"))

    return presentation_metrics


def _fallback_marketing_summary(
    company_name: str,
    metrics: dict,
    flags: list[str],
    period_context: dict | None = None,
) -> str:
    """Build a deterministic fallback for marketing summary."""
    risk = metrics.get("marketing_risk", "bilinmiyor")
    total_spend = metrics.get("total_spend", 0)
    overall_roas = metrics.get("overall_roas", 0)
    low_roas_count = metrics.get("low_roas_campaign_count", 0)
    platforms = metrics.get("platform_summary", [])

    period_note = ""
    if period_context and period_context.get("data_coverage_note"):
        period_note = (
            f"Not: {period_context['data_coverage_note']} Bu nedenle pazarlama yorumu "
            "eldeki veri kapsamıyla sınırlıdır."
        )

    efficiency_text = "Reklam verimliliği izlenebilir seviyede görünüyor."
    if "low_marketing_efficiency" in flags:
        efficiency_text = "Reklam harcaması gelir üretme verimliliği açısından baskı altında."
    elif "low_roas_campaigns" in flags:
        efficiency_text = "Bazı kampanyalar düşük ROAS nedeniyle optimizasyon gerektiriyor."

    platform_text = ""
    if platforms:
        worst_platform = sorted(platforms, key=lambda x: x.get("roas", 0))[0]
        platform_text = f"En zayıf platform {worst_platform.get('platform')} olarak görünüyor."
    else:
        platform_text = "Platform bazlı karşılaştırma için yeterli kırılım bulunmuyor."

    return "\n".join(
        [
            f"Pazarlama özeti: {company_name} için pazarlama riski {risk} seviyesinde görünüyor.",
            "",
            "Bulgular:",
            f"- Toplam reklam harcaması {_format_money(total_spend)}, genel ROAS {_format_ratio(overall_roas)}.",
            f"- Düşük ROAS kampanya sayısı {low_roas_count}. {efficiency_text}",
            f"- {platform_text}",
            *(["", period_note] if period_note else []),
            "",
            "Öneriler:",
            "1. Bugün: Düşük ROAS kampanyaları yeni bütçe artırımlarından önce durdurma, azaltma veya test listesine alın.",
            "2. Bugün: Bütçeyi yalnızca ölçülebilir gelir katkısı olan kampanyalara yönlendirin.",
            "3. Bu hafta: Platform ve kampanya bazında ROAS, CAC ve dönüşüm kalitesini birlikte izleyen optimizasyon planı çıkarın.",
        ]
    )


def _invoke_data_tool(tool, payload: dict, tool_name: str):
    """Invoke a data tool and log failures before re-raising."""
    try:
        return tool.invoke(payload)
    except Exception as exc:
        logger.exception("Data tool failed [%s]: %s", tool_name, exc)
        raise


def _invoke_llm_tool_with_fallback(tool, payload: dict, fallback_value: str, tool_name: str) -> str:
    """Invoke an LLM tool or return a deterministic fallback."""
    try:
        return tool.invoke(payload)
    except Exception as exc:
        logger.warning("LLM tool failed [%s]: %s. Falling back to deterministic summary.", tool_name, exc)
        return fallback_value


def marketing_agent_node(state: dict) -> dict:
    """Marketing agent node for the service workflow."""
    company_id = state["company_id"]
    company_name = state.get("company_name") or company_id
    user_question = state["user_question"]
    analysis_mode = state.get("analysis_mode", "domain_marketing")

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
        logger.warning("Could not create marketing agent run: %s", exc)

    try:
        period_context = resolve_agent_period(
            agent_name="marketing",
            question=user_question,
        )

        campaigns = _invoke_data_tool(
            get_recent_marketing_campaigns_tool,
            {
                "company_id": company_id,
                "days": period_context["effective_period_days"],
                "start_date": period_context.get("effective_start_date"),
                "end_date": period_context.get("effective_end_date"),
            },
            "get_recent_marketing_campaigns_tool",
        )

        marketing_period_context = build_data_coverage_context(
            rows=campaigns,
            date_field="campaign_start_at",
            period_context=period_context,
        )

        raw_metrics = compute_marketing_metrics_tool.invoke({"campaigns": campaigns})
        marketing_flags = build_marketing_flags(raw_metrics)
        presentation_metrics = _build_presentation_metrics(raw_metrics)

        summary: str | None = None
        if analysis_mode == "domain_marketing":
            fallback_summary = _fallback_marketing_summary(
                company_name=company_name,
                metrics=presentation_metrics,
                flags=marketing_flags,
                period_context=marketing_period_context,
            )
            summary = _invoke_llm_tool_with_fallback(
                generate_marketing_summary_tool,
                {
                    "company_name": company_name,
                    "metrics": presentation_metrics,
                    "latest_risk_score": None,
                    "user_question": user_question,
                    "period_context": marketing_period_context,
                },
                fallback_summary,
                "generate_marketing_summary_tool",
            )

        contract = build_agent_output_contract(
            agent_name=AGENT_NAME,
            metrics=raw_metrics,
            flags=marketing_flags,
            summary=summary,
            confidence=agent_confidence(
                has_data=bool(campaigns),
                base=0.91,
            ),
            data_coverage=marketing_period_context,
        )

        output = MarketingAgentOutput(
            contract=contract,
            marketing_metrics=raw_metrics,
            marketing_flags=marketing_flags,
            marketing_summary=summary,
        )

        persist_ok = True
        if agent_run_id:
            try:
                save_agent_output(
                    company_id=company_id,
                    agent_run_id=agent_run_id,
                    agent_name=AGENT_NAME,
                    output_type="marketing_domain_analysis",
                    summary=summary or "Pazarlama metrikleri, uyarılar ve dönem kapsamı üretildi.",
                    output_json={
                        "contract": output.dict(),
                        "standard_contract": contract.dict(),
                        "presentation_metrics": presentation_metrics,
                        "period_context": marketing_period_context,
                    },
                    confidence_score=0.91,
                )
            except Exception as exc:
                persist_ok = False
                logger.warning("Could not persist marketing agent output: %s", exc)

            try:
                complete_agent_run(agent_run_id, status="completed" if persist_ok else "failed")
            except Exception as exc:
                logger.warning("Could not finalize marketing agent run: %s", exc)

        return {
            **state,
            "marketing_output": output.dict(),
            "marketing_metrics": raw_metrics,
            "marketing_metrics_presentation": presentation_metrics,
            "marketing_flags": marketing_flags,
            "marketing_summary": summary,
            "marketing_period_context": marketing_period_context,
            "marketing_contract": contract.dict(),
            "agent_contracts": merge_agent_contracts(state, contract),
            "agent_run_id": agent_run_id,
        }

    except Exception:
        if agent_run_id:
            try:
                complete_agent_run(agent_run_id, status="failed")
            except Exception as exc:
                logger.warning("Could not mark marketing agent run as failed: %s", exc)
        raise
