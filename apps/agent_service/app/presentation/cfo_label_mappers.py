from __future__ import annotations


RISK_LABEL_TR = {
    "low": "düşük",
    "medium": "orta",
    "high": "yüksek",
    "critical": "kritik",
    "dusuk": "düşük",
    "yuksek": "yüksek",
}


def map_risk_label_tr(value: str | None) -> str:
    """Map risk label tr into a user-facing label."""
    if not value:
        return "bilinmiyor"
    return RISK_LABEL_TR.get(value, value)
