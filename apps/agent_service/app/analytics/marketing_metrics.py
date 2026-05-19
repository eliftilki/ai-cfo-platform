from __future__ import annotations

from decimal import Decimal


def _to_decimal(value) -> Decimal:
    """Convert a raw numeric value into a Decimal."""
    return Decimal(str(value or 0))


def compute_marketing_metrics(campaigns: list[dict]) -> dict:
    """Compute marketing metrics from normalized input data."""
    total_spend = Decimal("0")
    total_revenue = Decimal("0")
    total_clicks = 0
    total_impressions = 0
    total_conversions = 0
    total_attributed_orders = 0

    platform_buckets: dict[str, dict] = {}
    low_roas_campaigns: list[dict] = []

    for campaign in campaigns:
        platform = campaign.get("platform", "unknown")
        spend = _to_decimal(campaign.get("ad_spend"))
        revenue = _to_decimal(campaign.get("attributed_revenue"))
        clicks = int(campaign.get("clicks", 0))
        impressions = int(campaign.get("impressions", 0))
        conversions = int(campaign.get("conversions", 0))
        orders = int(campaign.get("attributed_orders", 0))
        roas = _to_decimal(campaign.get("roas"))
        cac = _to_decimal(campaign.get("cac"))

        total_spend += spend
        total_revenue += revenue
        total_clicks += clicks
        total_impressions += impressions
        total_conversions += conversions
        total_attributed_orders += orders

        if platform not in platform_buckets:
            platform_buckets[platform] = {
                "platform": platform,
                "spend": Decimal("0"),
                "revenue": Decimal("0"),
                "clicks": 0,
                "impressions": 0,
                "conversions": 0,
                "orders": 0,
            }

        platform_buckets[platform]["spend"] += spend
        platform_buckets[platform]["revenue"] += revenue
        platform_buckets[platform]["clicks"] += clicks
        platform_buckets[platform]["impressions"] += impressions
        platform_buckets[platform]["conversions"] += conversions
        platform_buckets[platform]["orders"] += orders

        if roas < Decimal("1.5"):
            low_roas_campaigns.append(
                {
                    "campaign_name": campaign.get("campaign_name"),
                    "platform": platform,
                    "roas": float(roas),
                    "ad_spend": float(spend),
                    "attributed_revenue": float(revenue),
                    "cac": float(cac),
                }
            )

    overall_roas = float(total_revenue / total_spend) if total_spend > 0 else 0.0
    overall_cac = float(total_spend / total_attributed_orders) if total_attributed_orders > 0 else 0.0

    platform_summary = []
    for bucket in platform_buckets.values():
        spend = bucket["spend"]
        revenue = bucket["revenue"]
        orders = bucket["orders"]

        platform_summary.append(
            {
                "platform": bucket["platform"],
                "spend": float(spend),
                "revenue": float(revenue),
                "roas": float(revenue / spend) if spend > 0 else 0.0,
                "cac": float(spend / orders) if orders > 0 else 0.0,
                "clicks": bucket["clicks"],
                "impressions": bucket["impressions"],
                "conversions": bucket["conversions"],
                "orders": orders,
            }
        )

    platform_summary.sort(key=lambda x: x["spend"], reverse=True)
    low_roas_campaigns.sort(key=lambda x: x["roas"])

    if overall_roas >= 3:
        marketing_risk = "low"
    elif overall_roas >= 2:
        marketing_risk = "medium"
    elif overall_roas >= 1.2:
        marketing_risk = "high"
    else:
        marketing_risk = "critical"

    return {
        "campaign_count": len(campaigns),
        "total_spend": float(total_spend),
        "total_attributed_revenue": float(total_revenue),
        "overall_roas": overall_roas,
        "overall_cac": overall_cac,
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "total_conversions": total_conversions,
        "total_attributed_orders": total_attributed_orders,
        "marketing_risk": marketing_risk,
        "platform_summary": platform_summary,
        "low_roas_campaigns": low_roas_campaigns[:5],
        "low_roas_campaign_count": len(low_roas_campaigns),
    }