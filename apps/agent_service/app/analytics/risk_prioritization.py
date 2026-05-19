from __future__ import annotations

from decimal import Decimal


RISK_NUMERIC_MAP = {
    "low": 15,
    "medium": 35,
    "high": 60,
    "critical": 85,
    "dusuk": 15,
    "orta": 35,
    "yuksek": 60,
    "kritik": 85,
}


def normalize_risk_value(value: str | None) -> int:
    """Normalize risk value into the platform data model."""
    if not value:
        return 0
    return RISK_NUMERIC_MAP.get(str(value).strip().lower(), 0)


def risk_level_from_score(score: int) -> str:
    """Risk level from score for the service workflow."""
    if score < 25:
        return "low"
    if score < 50:
        return "medium"
    if score < 75:
        return "high"
    return "critical"


def build_cashflow_flags(metrics: dict | None) -> list[str]:
    """Build cashflow flags for downstream service or UI use."""
    if not metrics:
        return ["cashflow_data_unavailable"]

    flags: list[str] = []
    net_30 = Decimal(str(metrics.get("net_cashflow_30d", 0)))
    net_7 = Decimal(str(metrics.get("net_cashflow_7d", 0)))
    expense_30 = Decimal(str(metrics.get("expense_30d", 0)))
    income_30 = Decimal(str(metrics.get("income_30d", 0)))
    liquidity_risk = str(metrics.get("liquidity_risk") or "").lower()

    if net_30 < 0:
        flags.append("negative_30d_cashflow")
    if net_7 < 0:
        flags.append("negative_7d_cashflow")
    if expense_30 > income_30 and income_30 > 0:
        flags.append("expense_pressure")
    if liquidity_risk in {"high", "critical"}:
        flags.append("liquidity_pressure")
    if metrics.get("top_expense_categories_30d"):
        flags.append("concentrated_outflows")

    return flags


def build_marketing_flags(metrics: dict | None) -> list[str]:
    """Build marketing flags for downstream service or UI use."""
    if not metrics:
        return ["marketing_data_unavailable"]

    flags: list[str] = []
    roas = Decimal(str(metrics.get("overall_roas", 0)))
    low_roas_count = int(metrics.get("low_roas_campaign_count", 0))
    marketing_risk = str(metrics.get("marketing_risk") or "").lower()

    if roas < Decimal("1.5"):
        flags.append("low_marketing_efficiency")
    if low_roas_count > 0:
        flags.append("low_roas_campaigns")
    if low_roas_count >= 5:
        flags.append("multiple_low_roas_campaigns")
    if marketing_risk in {"high", "critical"}:
        flags.append("marketing_spend_risk")

    return flags


def build_priority_actions(
    cashflow_metrics: dict | None,
    marketing_metrics: dict | None,
    top_risk_factors: list[str],
) -> list[str]:
    """Build priority actions for downstream service or UI use."""
    actions: list[str] = []

    if "negative_30d_cashflow" in top_risk_factors or "liquidity_pressure" in top_risk_factors:
        actions.append("Bugün: Kritik olmayan nakit çıkışlarını dondurun veya önümüzdeki 30 gün için yeniden takvimlendirin.")
    if "expense_pressure" in top_risk_factors or "concentrated_outflows" in top_risk_factors:
        actions.append("Bugün: En büyük gider kategorilerini gözden geçirip haftalık ödeme önceliklerini belirleyin.")
    if "low_marketing_efficiency" in top_risk_factors or "marketing_spend_risk" in top_risk_factors:
        actions.append("Bu hafta: Düşük ROAS kampanyalarında bütçeyi azaltıp harcamayı daha verimli kanallara kaydırın.")
    if "multiple_low_roas_campaigns" in top_risk_factors:
        actions.append("Bu hafta: Her düşük performanslı kampanya için sorumlu kişi, bütçe kararı ve son tarih içeren aksiyon listesi oluşturun.")

    if cashflow_metrics and marketing_metrics:
        net_30 = Decimal(str(cashflow_metrics.get("net_cashflow_30d", 0)))
        roas = Decimal(str(marketing_metrics.get("overall_roas", 0)))
        if net_30 < 0 and roas < Decimal("1.5"):
            actions.insert(0, "Bugün: Pazarlama bütçesi artışlarını ölçülebilir nakit toparlanması görülene kadar durdurun.")

    if not actions:
        actions.append("Bu hafta: Likidite, pazarlama verimliliği ve risk hareketini haftalık yönetim takibine alın.")

    return actions[:5]
