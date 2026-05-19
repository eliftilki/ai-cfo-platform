from __future__ import annotations

from app.analytics.risk_prioritization import (
    build_cashflow_flags,
    build_marketing_flags,
    build_priority_actions,
    normalize_risk_value,
    risk_level_from_score,
)


def compute_combined_risk_assessment(
    cashflow_metrics: dict | None,
    marketing_metrics: dict | None,
    latest_risk_score: dict | None = None,
) -> dict:
    """Compute combined risk assessment from normalized input data."""
    cashflow_component = 0
    marketing_component = 0
    stored_component = 0
    top_risk_factors: list[str] = []

    if cashflow_metrics:
        liquidity_risk = cashflow_metrics.get("liquidity_risk")
        cashflow_component = normalize_risk_value(liquidity_risk)
        top_risk_factors.extend(build_cashflow_flags(cashflow_metrics))

    if marketing_metrics:
        marketing_risk = marketing_metrics.get("marketing_risk")
        marketing_component = normalize_risk_value(marketing_risk)
        top_risk_factors.extend(build_marketing_flags(marketing_metrics))

    if latest_risk_score:
        stored_component = int(latest_risk_score.get("overall_risk_score", 0))

        for factor in latest_risk_score.get("top_risk_factors", []):
            if factor not in top_risk_factors:
                top_risk_factors.append(factor)

    weights = {
        "cashflow": 0.5,
        "marketing": 0.3,
        "stored": 0.2,
    }

    overall_score = int(
        (cashflow_component * weights["cashflow"]) +
        (marketing_component * weights["marketing"]) +
        (stored_component * weights["stored"])
    )

    risk_level = risk_level_from_score(overall_score)
    deduped_factors = list(dict.fromkeys(top_risk_factors))[:5]

    return {
        "overall_risk_score": overall_score,
        "overall_risk_level": risk_level,
        "cashflow_component": cashflow_component,
        "marketing_component": marketing_component,
        "stored_component": stored_component,
        "top_risk_factors": deduped_factors,
        "priority_actions": build_priority_actions(
            cashflow_metrics=cashflow_metrics,
            marketing_metrics=marketing_metrics,
            top_risk_factors=deduped_factors,
        ),
    }
