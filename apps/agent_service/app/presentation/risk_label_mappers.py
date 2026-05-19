from __future__ import annotations


RISK_LABEL_TR = {
    "low": "düşük",
    "medium": "orta",
    "high": "yüksek",
    "critical": "kritik",
    "dusuk": "düşük",
    "yuksek": "yüksek",
}


RISK_FACTOR_LABEL_TR = {
    "negative_30d_cashflow": "Son 30 günde negatif net nakit akışı",
    "negative_7d_cashflow": "Son 7 günde negatif net nakit akışı",
    "expense_pressure": "Gider baskısı yüksek",
    "liquidity_pressure": "Likidite baskısı var",
    "concentrated_outflows": "Nakit çıkışları belirli giderlerde yoğunlaşıyor",
    "high_operating_outflows": "Yüksek operasyonel nakit çıkışları",
    "low_marketing_efficiency": "Düşük reklam verimliliği",
    "low_roas_campaigns": "Düşük ROAS kampanyalar var",
    "multiple_low_roas_campaigns": "Çok sayıda düşük ROAS kampanyası",
    "marketing_spend_risk": "Pazarlama harcaması riski yüksek",
    "critical_liquidity_pressure": "Kritik likidite baskısı",
    "marketing_limited_data_coverage": "Pazarlama veri kapsamı sınırlı",
    "cashflow_limited_data_coverage": "Nakit akışı veri kapsamı sınırlı",
    "cashflow_low_confidence": "Nakit akışı analiz güveni sınırlı",
    "marketing_low_confidence": "Pazarlama analiz güveni sınırlı",
    "data_quality_warning": "Veri kalitesi uyarısı",
    "fx_pressure": "kur baskisi",
}


def map_risk_label_tr(value: str | None) -> str:
    """Map risk label tr into a user-facing label."""
    if not value:
        return "bilinmiyor"
    return RISK_LABEL_TR.get(value, value)


def map_risk_factor_label_tr(value: str | None) -> str:
    """Map risk factor label tr into a user-facing label."""
    if not value:
        return "bilinmiyor"
    return RISK_FACTOR_LABEL_TR.get(value, value)
