from __future__ import annotations

import logging
from copy import deepcopy

from app.analytics.risk_prioritization import build_cashflow_flags
from app.agents.output_contracts import agent_confidence, build_agent_output_contract, merge_agent_contracts
from app.orchestration.data_coverage import build_data_coverage_context
from app.orchestration.time_context import resolve_agent_period
from app.presentation.label_mappers import map_category_label_tr, map_risk_label_tr
from app.schemas.agent_outputs import CashflowAgentOutput
from app.services.supabase_service import create_agent_run, complete_agent_run, save_agent_output
from app.tools.analytics_tools import compute_cashflow_metrics_tool
from app.tools.data_tools import (
    get_latest_cashflow_snapshot_tool,
    get_recent_bank_transactions_tool,
)
from app.tools.llm_tools import generate_cashflow_summary_tool


AGENT_NAME = "cashflow_agent"
logger = logging.getLogger(__name__)


def _format_money(value) -> str:
    """Format a numeric value for Turkish business-facing summaries."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{number:,.0f} TL".replace(",", ".")


def _build_presentation_metrics(metrics: dict) -> dict:
    """Build presentation metrics for downstream service or UI use."""
    presentation_metrics = deepcopy(metrics)

    presentation_metrics["liquidity_risk"] = map_risk_label_tr(
        presentation_metrics.get("liquidity_risk")
    )

    for item in presentation_metrics.get("top_expense_categories_30d", []):
        item["category"] = map_category_label_tr(item.get("category"))

    for item in presentation_metrics.get("top_income_categories_30d", []):
        item["category"] = map_category_label_tr(item.get("category"))

    return presentation_metrics


def _fallback_cashflow_summary(
    company_name: str,
    metrics: dict,
    flags: list[str],
    period_context: dict | None = None,
) -> str:
    """Build a deterministic fallback for cashflow summary."""
    liquidity_risk = metrics.get("liquidity_risk", "bilinmiyor")
    net_30 = metrics.get("net_cashflow_30d", 0)
    income_30 = metrics.get("income_30d", 0)
    expense_30 = metrics.get("expense_30d", 0)
    top_expenses = metrics.get("top_expense_categories_30d", [])

    period_note = ""
    if period_context and period_context.get("data_coverage_note"):
        period_note = (
            f"Not: {period_context['data_coverage_note']} Bu nedenle yorumlar "
            "eldeki veri kapsamıyla sınırlıdır."
        )

    pressure_text = "Nakit akışı kendi domaini içinde izlenebilir seviyede görünüyor."
    if "negative_30d_cashflow" in flags:
        pressure_text = "İncelenen dönemde negatif net nakit akışı likidite baskısı oluşturuyor."
    elif "expense_pressure" in flags:
        pressure_text = "Gider çıkışları gelir girişlerine göre daha baskın ilerliyor."

    category_text = ""
    if top_expenses:
        category_text = f"En büyük gider alanı {top_expenses[0].get('category')} olarak görünüyor."
    else:
        category_text = "Gider yoğunlaşması için yeterli kategori detayı bulunmuyor."

    return "\n".join(
        [
            f"Nakit akışı özeti: {company_name} için likidite riski {liquidity_risk} seviyesinde görünüyor.",
            "",
            "Bulgular:",
            f"- 30 günlük gelir {_format_money(income_30)}, gider {_format_money(expense_30)}, net nakit akışı {_format_money(net_30)}.",
            f"- {pressure_text}",
            f"- {category_text}",
            *(["", period_note] if period_note else []),
            "",
            "Öneriler:",
            "1. Bugün: Kritik ödemeleri ve tahsilat beklentilerini aynı kısa vadeli nakit planında önceliklendirin.",
            "2. Bugün: Negatif net nakit akışı devam ediyorsa zorunlu olmayan çıkışları geçici olarak durdurun veya yeniden takvimlendirin.",
            "3. Bu hafta: En büyük gider kategorileri için haftalık limit ve onay mekanizması oluşturun.",
        ]
    )


def _invoke_data_tool(tool, payload: dict, tool_name: str):
    """Invoke a data tool and log failures before re-raising."""
    try:
        return tool.invoke(payload)
    except Exception as exc:
        logger.exception("Data tool failed [%s]: %s", tool_name, exc)
        raise


def _invoke_llm_tool_with_fallback(
    tool,
    payload: dict,
    fallback_value: str,
    tool_name: str,
) -> str:
    """Invoke an LLM tool or return a deterministic fallback."""
    try:
        return tool.invoke(payload)
    except Exception as exc:
        logger.warning(
            "LLM tool failed [%s]: %s. Falling back to deterministic summary.",
            tool_name,
            exc,
        )
        return fallback_value


def cashflow_agent_node(state: dict) -> dict:
    """
    Domain agent: analyzes cashflow data and emits a bounded contract.

    Behavior:
    - Domain-only cashflow question:
        metrics + flags + period_context + summary
    - Full-chain / executive question:
        metrics + flags + period_context only
        summary remains None, because CFO layer generates the final answer.
    """

    company_id = state["company_id"]
    company_name = state.get("company_name") or company_id
    user_question = state["user_question"]
    analysis_mode = state.get("analysis_mode", "domain_cashflow")

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
        logger.warning("Could not create cashflow agent run: %s", exc)

    try:
        period_context = resolve_agent_period(
            agent_name="cashflow",
            question=user_question,
        )

        bank_transactions = _invoke_data_tool(
            get_recent_bank_transactions_tool,
            {
                "company_id": company_id,
                "days": period_context["effective_period_days"],
                "start_date": period_context.get("effective_start_date"),
                "end_date": period_context.get("effective_end_date"),
            },
            "get_recent_bank_transactions_tool",
        )

        cashflow_period_context = build_data_coverage_context(
            rows=bank_transactions,
            date_field="transaction_date",
            period_context=period_context,
        )

        latest_snapshot = _invoke_data_tool(
            get_latest_cashflow_snapshot_tool,
            {"company_id": company_id},
            "get_latest_cashflow_snapshot_tool",
        )

        raw_metrics = compute_cashflow_metrics_tool.invoke(
            {"bank_transactions": bank_transactions}
        )

        cashflow_flags = build_cashflow_flags(raw_metrics)
        presentation_metrics = _build_presentation_metrics(raw_metrics)

        summary: str | None = None

        if analysis_mode == "domain_cashflow":
            fallback_summary = _fallback_cashflow_summary(
                company_name=company_name,
                metrics=presentation_metrics,
                flags=cashflow_flags,
                period_context=cashflow_period_context,
            )

            summary = _invoke_llm_tool_with_fallback(
                generate_cashflow_summary_tool,
                {
                    "company_name": company_name,
                    "metrics": presentation_metrics,
                    "latest_snapshot": latest_snapshot,
                    "latest_risk_score": None,
                    "user_question": user_question,
                    "period_context": cashflow_period_context,
                },
                fallback_summary,
                "generate_cashflow_summary_tool",
            )

        contract = build_agent_output_contract(
            agent_name=AGENT_NAME,
            metrics=raw_metrics,
            flags=cashflow_flags,
            summary=summary,
            confidence=agent_confidence(
                has_data=bool(bank_transactions),
                base=0.92,
            ),
            data_coverage=cashflow_period_context,
        )

        output = CashflowAgentOutput(
            contract=contract,
            cashflow_metrics=raw_metrics,
            cashflow_flags=cashflow_flags,
            cashflow_summary=summary,
            latest_cashflow_snapshot=latest_snapshot,
        )

        persist_ok = True

        if agent_run_id:
            try:
                save_agent_output(
                    company_id=company_id,
                    agent_run_id=agent_run_id,
                    agent_name=AGENT_NAME,
                    output_type="cashflow_domain_analysis",
                    summary=summary or "Nakit akışı metrikleri, uyarılar ve dönem kapsamı üretildi.",
                    output_json={
                        "contract": output.dict(),
                        "standard_contract": contract.dict(),
                        "presentation_metrics": presentation_metrics,
                        "period_context": cashflow_period_context,
                    },
                    confidence_score=0.92,
                )
            except Exception as exc:
                persist_ok = False
                logger.warning("Could not persist cashflow agent output: %s", exc)

            try:
                complete_agent_run(
                    agent_run_id,
                    status="completed" if persist_ok else "failed",
                )
            except Exception as exc:
                logger.warning("Could not finalize cashflow agent run: %s", exc)

        return {
            **state,
            "bank_transactions": bank_transactions,
            "cashflow_output": output.dict(),
            "cashflow_metrics": raw_metrics,
            "cashflow_metrics_presentation": presentation_metrics,
            "cashflow_flags": cashflow_flags,
            "latest_cashflow_snapshot": latest_snapshot,
            "cashflow_summary": summary,
            "cashflow_period_context": cashflow_period_context,
            "cashflow_contract": contract.dict(),
            "agent_contracts": merge_agent_contracts(state, contract),
            "agent_run_id": agent_run_id,
        }

    except Exception:
        if agent_run_id:
            try:
                complete_agent_run(agent_run_id, status="failed")
            except Exception as exc:
                logger.warning("Could not mark cashflow agent run as failed: %s", exc)

        raise
