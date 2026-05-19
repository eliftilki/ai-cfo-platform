from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from packages.contracts.python.simulation_contracts import SimulationRequest


def _to_decimal(value: Any) -> Decimal:
    """Convert a raw numeric value into a Decimal."""
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _to_float(value: Decimal) -> float:
    """Convert a Decimal value into a plain float."""
    return float(round(value, 2))


def _format_money(value: Decimal) -> str:
    """Format a Decimal as a Turkish business-facing money value."""
    return f"{float(round(value, 0)):,.0f} TL".replace(",", ".")


def _clamp(value: int, min_value: int, max_value: int) -> int:
    """Clamp a numeric value into the provided inclusive range."""
    return max(min_value, min(max_value, value))


def _risk_level_from_score(score: int) -> str:
    """Convert a numeric risk score into a risk level label."""
    if score < 25:
        return "low"
    if score < 50:
        return "medium"
    if score < 75:
        return "high"
    return "critical"


def compute_base_cashflow_context(bank_transactions: list[dict]) -> dict:
    """Compute base cashflow context from normalized input data."""
    income = Decimal("0")
    expense = Decimal("0")
    expense_by_category: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    income_by_category: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for tx in bank_transactions:
        amount = abs(_to_decimal(tx.get("amount")))
        direction = tx.get("direction")
        category = tx.get("category") or "uncategorized"

        if direction == "income":
            income += amount
            income_by_category[category] += amount
        elif direction == "expense":
            expense += amount
            expense_by_category[category] += amount

    net_cashflow = income - expense

    return {
        "income": _to_float(income),
        "expense": _to_float(expense),
        "net_cashflow": _to_float(net_cashflow),
        "expense_by_category": {
            key: _to_float(value)
            for key, value in sorted(
                expense_by_category.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        },
        "income_by_category": {
            key: _to_float(value)
            for key, value in sorted(
                income_by_category.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        },
        "transaction_count": len(bank_transactions),
    }


def compute_base_marketing_context(campaigns: list[dict]) -> dict:
    """Compute base marketing context from normalized input data."""
    total_spend = Decimal("0")
    total_revenue = Decimal("0")
    low_roas_spend = Decimal("0")
    low_roas_revenue = Decimal("0")
    low_roas_count = 0

    for campaign in campaigns:
        spend = _to_decimal(campaign.get("ad_spend"))
        revenue = _to_decimal(campaign.get("attributed_revenue"))
        roas = _to_decimal(campaign.get("roas"))

        total_spend += spend
        total_revenue += revenue

        if roas > 0 and roas < Decimal("1.5"):
            low_roas_count += 1
            low_roas_spend += spend
            low_roas_revenue += revenue

    overall_roas = total_revenue / total_spend if total_spend > 0 else Decimal("0")

    return {
        "total_spend": _to_float(total_spend),
        "total_attributed_revenue": _to_float(total_revenue),
        "overall_roas": float(round(overall_roas, 4)),
        "low_roas_spend": _to_float(low_roas_spend),
        "low_roas_revenue": _to_float(low_roas_revenue),
        "low_roas_campaign_count": low_roas_count,
        "campaign_count": len(campaigns),
    }


def _estimate_risk_change(
    *,
    current_risk_score: int | None,
    net_cashflow_change: Decimal,
    revenue_change: Decimal,
    expense_change: Decimal,
) -> int:
    """Estimate risk change for internal workflow use."""
    risk_change = 0

    if net_cashflow_change > Decimal("1000000"):
        risk_change -= 12
    elif net_cashflow_change > Decimal("500000"):
        risk_change -= 8
    elif net_cashflow_change > Decimal("100000"):
        risk_change -= 4

    if net_cashflow_change < Decimal("-1000000"):
        risk_change += 12
    elif net_cashflow_change < Decimal("-500000"):
        risk_change += 8
    elif net_cashflow_change < Decimal("-100000"):
        risk_change += 4

    if revenue_change < Decimal("-500000"):
        risk_change += 4
    elif revenue_change < Decimal("-100000"):
        risk_change += 2

    if expense_change < Decimal("0"):
        risk_change -= 3

    if current_risk_score is not None and current_risk_score >= 75 and risk_change < 0:
        risk_change -= 2

    return _clamp(risk_change, -25, 25)


def _build_recommendation(
    *,
    scenario_type: str,
    revenue_change: Decimal,
    expense_change: Decimal,
    risk_change: int,
) -> str:
    """Build recommendation for downstream service or UI use."""
    if scenario_type == "marketing_budget_change":
        if expense_change < 0 and risk_change <= 0:
            return "Düşük verimli reklam harcamalarını kademeli azaltın; bütçe kesintisini ROAS takibiyle birlikte uygulayın."
        if revenue_change < 0:
            return "Bütçe değişikliğini tek seferde değil, kampanya bazlı test ederek uygulayın."
        return "Pazarlama bütçesi değişikliğini performansı yüksek kampanyalara odaklayarak uygulayın."

    if scenario_type == "supplier_payment_deferral":
        return "Tedarikçi ödemelerinde erteleme yapılacaksa kritik tedarikçileri hariç tutarak vade planı oluşturun."

    if scenario_type == "roas_improvement":
        return "ROAS hedefini düşük performanslı kampanyaları optimize ederek ve bütçeyi yüksek verimli kanallara kaydırarak takip edin."

    return "Senaryoyu uygulamadan önce nakit etkisini ve operasyonel riski birlikte değerlendirin."


def _build_summary(
    *,
    simulation_name: str,
    revenue_change: Decimal,
    expense_change: Decimal,
    net_cashflow_change: Decimal,
    risk_change: int,
    projected_risk_score: int | None,
) -> str:
    """Build summary for downstream service or UI use."""
    risk_direction = "azalması" if risk_change < 0 else "artması" if risk_change > 0 else "belirgin değişmemesi"
    net_tone = "iyileştiriyor" if net_cashflow_change > 0 else "zayıflatıyor" if net_cashflow_change < 0 else "nötr etkiliyor"

    risk_score_text = ""
    if projected_risk_score is not None:
        risk_score_text = f" Projeksiyona göre risk skoru yaklaşık {projected_risk_score}/100 seviyesine gelebilir."

    return "\n".join(
        [
            f"Simülasyon özeti: {simulation_name} senaryosu, net nakit akışını {_format_money(net_cashflow_change)} etkileyerek kısa vadeli görünümü {net_tone}.",
            "",
            "Projeksiyon:",
            f"- Gelir etkisi: {_format_money(revenue_change)}",
            f"- Gider etkisi: {_format_money(expense_change)}",
            f"- Net nakit akışı etkisi: {_format_money(net_cashflow_change)}",
            f"- Risk etkisi: riskin {risk_direction} beklenir.{risk_score_text}",
            "",
            "Yorum: Bu sonuç garanti tahmin değil, verilen varsayımlara göre hesaplanan deterministik bir senaryo projeksiyonudur.",
        ]
    )


def run_deterministic_simulation(
    *,
    request: SimulationRequest,
    cashflow_context: dict,
    marketing_context: dict,
    latest_risk_score: dict | None,
) -> dict:
    """Run deterministic simulation and return the resulting response."""
    scenario_type = request.scenario_type

    revenue_change = Decimal("0")
    expense_change = Decimal("0")

    if scenario_type == "marketing_budget_change":
        if request.marketing_budget_change_percent is None:
            raise ValueError("marketing_budget_change_percent is required for marketing_budget_change.")

        change_ratio = Decimal(str(request.marketing_budget_change_percent)) / Decimal("100")

        if request.marketing_scope == "low_roas_only":
            base_spend = _to_decimal(marketing_context.get("low_roas_spend"))
            base_revenue = _to_decimal(marketing_context.get("low_roas_revenue"))

            expense_change = base_spend * change_ratio

            if change_ratio < 0:
                revenue_change = base_revenue * change_ratio * Decimal("0.35")
            else:
                revenue_change = base_revenue * change_ratio * Decimal("0.75")
        else:
            base_spend = _to_decimal(marketing_context.get("total_spend"))
            base_revenue = _to_decimal(marketing_context.get("total_attributed_revenue"))

            expense_change = base_spend * change_ratio
            revenue_change = base_revenue * change_ratio

    elif scenario_type == "supplier_payment_deferral":
        if request.supplier_payment_deferral_days is None:
            raise ValueError("supplier_payment_deferral_days is required for supplier_payment_deferral.")

        ratio = Decimal(str(request.supplier_payment_deferral_ratio))
        ratio = max(Decimal("0"), min(Decimal("1"), ratio))

        expense_by_category = cashflow_context.get("expense_by_category", {})
        supplier_payments = _to_decimal(
            expense_by_category.get("supplier_payment")
            or expense_by_category.get("tedarikci odemeleri")
            or expense_by_category.get("tedarikçi ödemeleri")
            or 0
        )

        expense_change = -(supplier_payments * ratio)
        revenue_change = Decimal("0")

    elif scenario_type == "roas_improvement":
        if request.target_roas is None:
            raise ValueError("target_roas is required for roas_improvement.")

        total_spend = _to_decimal(marketing_context.get("total_spend"))
        current_revenue = _to_decimal(marketing_context.get("total_attributed_revenue"))
        target_revenue = total_spend * Decimal(str(request.target_roas))

        revenue_change = max(Decimal("0"), target_revenue - current_revenue)
        expense_change = Decimal("0")

    elif scenario_type == "custom_financial_change":
        revenue_change = _to_decimal(request.custom_revenue_change)
        expense_change = _to_decimal(request.custom_expense_change)

    else:
        raise ValueError(f"Unsupported scenario_type: {scenario_type}")

    net_cashflow_change = revenue_change - expense_change

    current_risk_score = None
    if latest_risk_score and latest_risk_score.get("overall_risk_score") is not None:
        current_risk_score = int(latest_risk_score["overall_risk_score"])

    risk_change = _estimate_risk_change(
        current_risk_score=current_risk_score,
        net_cashflow_change=net_cashflow_change,
        revenue_change=revenue_change,
        expense_change=expense_change,
    )

    projected_risk_score = None
    projected_risk_level = None

    if current_risk_score is not None:
        projected_risk_score = _clamp(current_risk_score + risk_change, 0, 100)
        projected_risk_level = _risk_level_from_score(projected_risk_score)

    recommended_action = _build_recommendation(
        scenario_type=scenario_type,
        revenue_change=revenue_change,
        expense_change=expense_change,
        risk_change=risk_change,
    )

    summary = _build_summary(
        simulation_name=request.simulation_name,
        revenue_change=revenue_change,
        expense_change=expense_change,
        net_cashflow_change=net_cashflow_change,
        risk_change=risk_change,
        projected_risk_score=projected_risk_score,
    )

    return {
        "predicted_revenue_change": _to_float(revenue_change),
        "predicted_expense_change": _to_float(expense_change),
        "predicted_net_cashflow_change": _to_float(net_cashflow_change),
        "predicted_risk_change": risk_change,
        "current_risk_score": current_risk_score,
        "projected_risk_score": projected_risk_score,
        "projected_risk_level": projected_risk_level,
        "recommended_action": recommended_action,
        "summary": summary,
    }
