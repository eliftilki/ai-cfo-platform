from __future__ import annotations


PLATFORM_LABEL_TR = {
    "meta": "Meta",
    "google_ads": "Google Ads",
    "unknown": "Bilinmeyen",
}


RISK_LABEL_TR = {
    "low": "düşük",
    "medium": "orta",
    "high": "yüksek",
    "critical": "kritik",
    "dusuk": "düşük",
    "yuksek": "yüksek",
}


def map_platform_label_tr(value: str | None) -> str:
    """Map platform label tr into a user-facing label."""
    if not value:
        return "Bilinmeyen"
    return PLATFORM_LABEL_TR.get(value, value)


def map_risk_label_tr(value: str | None) -> str:
    """Map risk label tr into a user-facing label."""
    if not value:
        return "bilinmiyor"
    return RISK_LABEL_TR.get(value, value)
