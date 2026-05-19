from __future__ import annotations

from datetime import datetime, timezone

from app.repositories.dashboard_repository import get_latest_dashboard_snapshot
from app.services.dashboard_refresh_service import refresh_company_dashboard
from packages.contracts.python.dashboard_contracts import DashboardOverviewResponse


UTC = timezone.utc


def _is_expired(expires_at: str | None) -> bool:
    """Is expired for internal workflow use."""
    if not expires_at:
        return True

    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return datetime.now(UTC) > parsed
    except ValueError:
        return True


def get_dashboard_overview(company_id: str) -> DashboardOverviewResponse:
    """Return dashboard overview."""
    snapshot = get_latest_dashboard_snapshot(company_id)

    refresh_status = "fresh"

    if not snapshot:
        snapshot = refresh_company_dashboard(company_id, force_full=True)
        refresh_status = "generated_on_demand"
    elif snapshot.get("is_stale") or _is_expired(snapshot.get("expires_at")):
        snapshot = refresh_company_dashboard(company_id, force_full=False)
        refresh_status = "generated_on_demand"

    data = snapshot.get("snapshot_json") or {}

    return DashboardOverviewResponse(
        company=data.get("company") or {"id": company_id, "name": None},
        period=data.get("period") or {"cashflow_days": 30, "marketing_days": 60},
        refresh_status=refresh_status,
        generated_at=snapshot.get("generated_at"),
        expires_at=snapshot.get("expires_at"),
        is_stale=bool(snapshot.get("is_stale", False)),
        data_freshness={
            "cashflow_data_last_seen_at": snapshot.get("cashflow_data_last_seen_at"),
            "marketing_data_last_seen_at": snapshot.get("marketing_data_last_seen_at"),
            "risk_score_last_seen_at": snapshot.get("risk_score_last_seen_at"),
            "alerts_last_seen_at": snapshot.get("alerts_last_seen_at"),
            "cashflow_refreshed_at": snapshot.get("cashflow_refreshed_at"),
            "marketing_refreshed_at": snapshot.get("marketing_refreshed_at"),
            "risk_refreshed_at": snapshot.get("risk_refreshed_at"),
            "alerts_refreshed_at": snapshot.get("alerts_refreshed_at"),
        },
        summary_cards=data.get("summary_cards") or {},
        cashflow=data.get("cashflow") or {},
        marketing=data.get("marketing") or {},
        risk=data.get("risk") or {},
        alerts=data.get("alerts") or {},
    )