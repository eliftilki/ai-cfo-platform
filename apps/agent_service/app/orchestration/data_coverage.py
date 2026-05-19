from __future__ import annotations

from datetime import datetime


def parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO timestamp into a datetime when possible."""
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_data_coverage_context(
    *,
    rows: list[dict],
    date_field: str,
    period_context: dict,
) -> dict:
    """Build data coverage context for downstream service or UI use."""
    dates: list[datetime] = []

    for row in rows:
        parsed = parse_datetime(row.get(date_field))
        if parsed:
            dates.append(parsed)

    if not dates:
        return {
            **period_context,
            "available_from": None,
            "available_to": None,
            "available_period_days": 0,
            "actual_period_days": 0,
            "data_coverage_note": (
                f"{period_context.get('period_note', '')} "
                "Bu analiz için ilgili dönemde veri bulunamadı."
            ).strip(),
        }

    min_date = min(dates)
    max_date = max(dates)

    available_period_days = max((max_date.date() - min_date.date()).days + 1, 1)
    effective_period_days = int(period_context.get("effective_period_days") or available_period_days)
    actual_period_days = min(available_period_days, effective_period_days)

    notes = []

    period_note = period_context.get("period_note")
    if period_note:
        notes.append(period_note)

    if actual_period_days < effective_period_days:
        notes.append(
            f"Ancak veritabanında bu analiz için yaklaşık son {actual_period_days} günlük veri bulundu; "
            "sonuçlar eldeki veri kapsamına göre üretilmiştir."
        )

    return {
        **period_context,
        "available_from": min_date.isoformat(),
        "available_to": max_date.isoformat(),
        "available_period_days": available_period_days,
        "actual_period_days": actual_period_days,
        "data_coverage_note": " ".join(notes).strip(),
    }