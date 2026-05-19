from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal


UTC = timezone.utc


def parse_dt(value: str) -> datetime:
    """Parse an ISO timestamp into a datetime when possible."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _to_decimal(value) -> Decimal:
    """Convert a raw numeric value into a Decimal."""
    return Decimal(str(value or 0))


def compute_cashflow_metrics(bank_transactions: list[dict]) -> dict:
    """Compute cashflow metrics from normalized input data."""
    now = datetime.now(UTC)
    last_7 = now - timedelta(days=7)
    last_14 = now - timedelta(days=14)
    last_30 = now - timedelta(days=30)

    income_7 = Decimal("0")
    expense_7 = Decimal("0")
    income_14 = Decimal("0")
    expense_14 = Decimal("0")
    income_30 = Decimal("0")
    expense_30 = Decimal("0")

    expense_by_category_30: dict[str, Decimal] = {}
    income_by_category_30: dict[str, Decimal] = {}

    for tx in bank_transactions:
        tx_dt = parse_dt(tx["transaction_date"])
        amount = _to_decimal(tx["amount"])
        direction = tx["direction"]
        category = tx.get("category") or "uncategorized"

        if tx_dt >= last_30:
            if direction == "income":
                income_30 += amount
                income_by_category_30.setdefault(category, Decimal("0"))
                income_by_category_30[category] += amount
            else:
                expense_30 += amount
                expense_by_category_30.setdefault(category, Decimal("0"))
                expense_by_category_30[category] += amount

        if tx_dt >= last_14:
            if direction == "income":
                income_14 += amount
            else:
                expense_14 += amount

        if tx_dt >= last_7:
            if direction == "income":
                income_7 += amount
            else:
                expense_7 += amount

    net_7 = income_7 - expense_7
    net_14 = income_14 - expense_14
    net_30 = income_30 - expense_30

    if net_30 > Decimal("50000"):
        liquidity_risk = "low"
    elif net_30 > Decimal("0"):
        liquidity_risk = "medium"
    elif net_30 > Decimal("-50000"):
        liquidity_risk = "high"
    else:
        liquidity_risk = "critical"

    top_expense_categories = sorted(
        (
            {"category": k, "amount": float(v)}
            for k, v in expense_by_category_30.items()
        ),
        key=lambda x: x["amount"],
        reverse=True,
    )[:5]

    top_income_categories = sorted(
        (
            {"category": k, "amount": float(v)}
            for k, v in income_by_category_30.items()
        ),
        key=lambda x: x["amount"],
        reverse=True,
    )[:5]

    return {
        "income_7d": float(income_7),
        "expense_7d": float(expense_7),
        "net_cashflow_7d": float(net_7),
        "income_14d": float(income_14),
        "expense_14d": float(expense_14),
        "net_cashflow_14d": float(net_14),
        "income_30d": float(income_30),
        "expense_30d": float(expense_30),
        "net_cashflow_30d": float(net_30),
        "liquidity_risk": liquidity_risk,
        "top_expense_categories_30d": top_expense_categories,
        "top_income_categories_30d": top_income_categories,
        "transaction_count_30d": len(
            [tx for tx in bank_transactions if parse_dt(tx["transaction_date"]) >= last_30]
        ),
    }