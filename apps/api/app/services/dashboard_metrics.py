from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any


def _to_decimal(value: Any) -> Decimal:
    """Convert a raw numeric value into a Decimal."""
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _to_float(value: Decimal) -> float:
    """Convert a Decimal value into a plain float."""
    return float(round(value, 2))


def compute_cashflow_dashboard_metrics(bank_transactions: list[dict]) -> dict:
    """Compute cashflow dashboard metrics from normalized input data."""
    income = Decimal("0")
    expense = Decimal("0")
    income_by_category: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    expense_by_category: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

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

    if net_cashflow < Decimal("-1000000"):
        liquidity_risk = "critical"
    elif net_cashflow < Decimal("0"):
        liquidity_risk = "high"
    elif income > 0 and expense / income > Decimal("0.85"):
        liquidity_risk = "medium"
    else:
        liquidity_risk = "low"

    top_expense_categories = [
        {"category": k, "amount": _to_float(v)}
        for k, v in sorted(expense_by_category.items(), key=lambda item: item[1], reverse=True)[:5]
    ]

    top_income_categories = [
        {"category": k, "amount": _to_float(v)}
        for k, v in sorted(income_by_category.items(), key=lambda item: item[1], reverse=True)[:5]
    ]

    return {
        "income": _to_float(income),
        "expense": _to_float(expense),
        "net_cashflow": _to_float(net_cashflow),
        "liquidity_risk": liquidity_risk,
        "transaction_count": len(bank_transactions),
        "top_expense_categories": top_expense_categories,
        "top_income_categories": top_income_categories,
    }


def compute_marketing_dashboard_metrics(campaigns: list[dict]) -> dict:
    """Compute marketing dashboard metrics from normalized input data."""
    spend = Decimal("0")
    revenue = Decimal("0")
    clicks = 0
    impressions = 0
    conversions = 0
    attributed_orders = 0

    by_platform: dict[str, dict[str, Any]] = {}

    low_roas_campaigns: list[dict] = []

    for campaign in campaigns:
        platform = campaign.get("platform") or "unknown"

        ad_spend = _to_decimal(campaign.get("ad_spend"))
        attributed_revenue = _to_decimal(campaign.get("attributed_revenue"))
        campaign_clicks = int(campaign.get("clicks") or 0)
        campaign_impressions = int(campaign.get("impressions") or 0)
        campaign_conversions = int(campaign.get("conversions") or 0)
        campaign_orders = int(campaign.get("attributed_orders") or 0)

        spend += ad_spend
        revenue += attributed_revenue
        clicks += campaign_clicks
        impressions += campaign_impressions
        conversions += campaign_conversions
        attributed_orders += campaign_orders

        if platform not in by_platform:
            by_platform[platform] = {
                "platform": platform,
                "spend": Decimal("0"),
                "revenue": Decimal("0"),
                "clicks": 0,
                "impressions": 0,
                "conversions": 0,
                "orders": 0,
            }

        by_platform[platform]["spend"] += ad_spend
        by_platform[platform]["revenue"] += attributed_revenue
        by_platform[platform]["clicks"] += campaign_clicks
        by_platform[platform]["impressions"] += campaign_impressions
        by_platform[platform]["conversions"] += campaign_conversions
        by_platform[platform]["orders"] += campaign_orders

        roas = Decimal(str(campaign.get("roas") or 0))
        if roas and roas < Decimal("1.5"):
            low_roas_campaigns.append(
                {
                    "campaign_name": campaign.get("campaign_name"),
                    "platform": platform,
                    "roas": float(roas),
                    "ad_spend": _to_float(ad_spend),
                    "attributed_revenue": _to_float(attributed_revenue),
                    "cac": float(campaign.get("cac") or 0),
                }
            )

    overall_roas = revenue / spend if spend > 0 else Decimal("0")
    overall_cac = spend / Decimal(conversions) if conversions > 0 else Decimal("0")

    if overall_roas < Decimal("1.2"):
        marketing_risk = "critical"
    elif overall_roas < Decimal("1.5"):
        marketing_risk = "high"
    elif overall_roas < Decimal("2.0"):
        marketing_risk = "medium"
    else:
        marketing_risk = "low"

    platform_summary = []
    for item in by_platform.values():
        platform_spend = item["spend"]
        platform_revenue = item["revenue"]
        platform_conversions = item["conversions"]

        platform_summary.append(
            {
                "platform": item["platform"],
                "spend": _to_float(platform_spend),
                "revenue": _to_float(platform_revenue),
                "roas": float(round(platform_revenue / platform_spend, 4)) if platform_spend > 0 else 0,
                "cac": float(round(platform_spend / Decimal(platform_conversions), 2)) if platform_conversions > 0 else 0,
                "clicks": item["clicks"],
                "impressions": item["impressions"],
                "conversions": item["conversions"],
                "orders": item["orders"],
            }
        )

    platform_summary.sort(key=lambda x: x["spend"], reverse=True)
    low_roas_campaigns.sort(key=lambda x: x["roas"])

    return {
        "campaign_count": len(campaigns),
        "total_spend": _to_float(spend),
        "total_attributed_revenue": _to_float(revenue),
        "overall_roas": float(round(overall_roas, 4)),
        "overall_cac": float(round(overall_cac, 2)),
        "total_clicks": clicks,
        "total_impressions": impressions,
        "total_conversions": conversions,
        "total_attributed_orders": attributed_orders,
        "marketing_risk": marketing_risk,
        "platform_summary": platform_summary,
        "low_roas_campaigns": low_roas_campaigns[:5],
        "low_roas_campaign_count": len(low_roas_campaigns),
    }


def build_summary_cards(
    *,
    cashflow_metrics: dict,
    marketing_metrics: dict,
    latest_risk_score: dict | None,
    alerts_summary: dict,
) -> dict:
    """Build summary cards for downstream service or UI use."""
    return {
        "net_cashflow_30d": cashflow_metrics.get("net_cashflow"),
        "income_30d": cashflow_metrics.get("income"),
        "expense_30d": cashflow_metrics.get("expense"),
        "liquidity_risk": cashflow_metrics.get("liquidity_risk"),

        "overall_roas": marketing_metrics.get("overall_roas"),
        "overall_cac": marketing_metrics.get("overall_cac"),
        "marketing_risk": marketing_metrics.get("marketing_risk"),

        "overall_risk_score": latest_risk_score.get("overall_risk_score") if latest_risk_score else None,
        "overall_risk_level": latest_risk_score.get("risk_level") if latest_risk_score else None,

        "unread_alert_count": alerts_summary.get("unread_count", 0),
        "critical_alert_count": alerts_summary.get("critical_count", 0),
    }