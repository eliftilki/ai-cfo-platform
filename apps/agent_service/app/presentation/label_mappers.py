from __future__ import annotations


RISK_LABEL_TR = {
    "low": "düşük",
    "medium": "orta",
    "high": "yüksek",
    "critical": "kritik",
    "dusuk": "düşük",
    "yuksek": "yüksek",
}


CATEGORY_LABEL_TR = {
    "sales_settlement": "satış tahsilatları",
    "supplier_payment": "tedarikçi ödemeleri",
    "ad_spend": "reklam harcamaları",
    "refund": "iade ödemeleri",
    "shipping": "kargo giderleri",
    "payroll": "personel giderleri",
    "tax": "vergi ödemeleri",
    "warehouse": "depo giderleri",
    "software": "yazılım giderleri",
    "rent": "kira giderleri",
    "operating_expense": "operasyonel giderler",
    "uncategorized": "diğer giderler",
}


def map_risk_label_tr(value: str | None) -> str:
    """Map risk label tr into a user-facing label."""
    if not value:
        return "bilinmiyor"
    return RISK_LABEL_TR.get(value, value)


def map_category_label_tr(value: str | None) -> str:
    """Map category label tr into a user-facing label."""
    if not value:
        return "diğer"
    return CATEGORY_LABEL_TR.get(value, value)
