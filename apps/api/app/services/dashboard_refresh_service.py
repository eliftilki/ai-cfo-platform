from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from app.repositories.dashboard_repository import (
    fetch_alerts,
    fetch_bank_transactions,
    fetch_company,
    fetch_latest_risk_score,
    fetch_marketing_campaigns,
    get_last_seen_at,
    get_latest_dashboard_snapshot,
    get_or_create_refresh_state,
    insert_dashboard_snapshot_history,
    list_company_ids_from_data,
    list_refresh_states,
    update_refresh_state,
    upsert_latest_dashboard_snapshot,
)
from app.services.dashboard_metrics import (
    build_summary_cards,
    compute_cashflow_dashboard_metrics,
    compute_marketing_dashboard_metrics,
)


UTC = timezone.utc

CASHFLOW_REFRESH_MINUTES = 15
MARKETING_REFRESH_MINUTES = 30
RISK_REFRESH_MINUTES = 60
ALERTS_REFRESH_MINUTES = 5
DAILY_SNAPSHOT_HOURS = 24

CASHFLOW_EVENT_THRESHOLD = 50
MARKETING_EVENT_THRESHOLD = 10
ALERT_EVENT_THRESHOLD = 1

CASHFLOW_DAYS = 30
MARKETING_DAYS = 60


DomainName = Literal["cashflow", "marketing", "risk", "alerts"]


def _now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


def _now_iso() -> str:
    """Return the current UTC timestamp as an ISO string."""
    return _now().isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO timestamp into a datetime when possible."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError:
        return None


def _minutes_since(value: str | None) -> float:
    """Minutes since for internal workflow use."""
    parsed = _parse_dt(value)
    if not parsed:
        return 999999
    return (_now() - parsed).total_seconds() / 60


def _hours_since(value: str | None) -> float:
    """Hours since for internal workflow use."""
    return _minutes_since(value) / 60


def _summarize_alerts(alerts: list[dict]) -> dict:
    """Summarize alerts for internal workflow use."""
    unread_count = sum(1 for alert in alerts if not alert.get("is_read"))
    critical_count = sum(1 for alert in alerts if alert.get("severity") == "critical")

    latest = [
        {
            "id": alert.get("id"),
            "alert_type": alert.get("alert_type"),
            "severity": alert.get("severity"),
            "title": alert.get("title"),
            "message": alert.get("message"),
            "is_read": alert.get("is_read"),
            "created_at": alert.get("created_at"),
        }
        for alert in alerts[:5]
    ]

    return {
        "unread_count": unread_count,
        "critical_count": critical_count,
        "latest": latest,
    }


def _build_snapshot_json(
    *,
    company_id: str,
    existing_snapshot_json: dict | None = None,
    refresh_domains: set[DomainName] | None = None,
) -> tuple[dict, dict]:
    """Build snapshot json for downstream service or UI use."""
    refresh_domains = refresh_domains or {"cashflow", "marketing", "risk", "alerts"}

    existing = existing_snapshot_json or {}

    company = fetch_company(company_id) or {"id": company_id, "name": None}

    cashflow_section = existing.get("cashflow", {})
    marketing_section = existing.get("marketing", {})
    risk_section = existing.get("risk", {})
    alerts_section = existing.get("alerts", {})

    cashflow_metrics = cashflow_section.get("metrics", {})
    marketing_metrics = marketing_section.get("metrics", {})
    latest_risk_score = risk_section.get("latest_score")
    alerts_summary = alerts_section

    if "cashflow" in refresh_domains:
        transactions = fetch_bank_transactions(company_id, days=CASHFLOW_DAYS)
        cashflow_metrics = compute_cashflow_dashboard_metrics(transactions)
        cashflow_section = {
            "metrics": cashflow_metrics,
            "top_expense_categories": cashflow_metrics.get("top_expense_categories", []),
            "top_income_categories": cashflow_metrics.get("top_income_categories", []),
            "transaction_count": cashflow_metrics.get("transaction_count", 0),
        }

    if "marketing" in refresh_domains:
        campaigns = fetch_marketing_campaigns(company_id, days=MARKETING_DAYS)
        marketing_metrics = compute_marketing_dashboard_metrics(campaigns)
        marketing_section = {
            "metrics": marketing_metrics,
            "platform_summary": marketing_metrics.get("platform_summary", []),
            "low_roas_campaigns": marketing_metrics.get("low_roas_campaigns", []),
            "campaign_count": marketing_metrics.get("campaign_count", 0),
        }

    if "risk" in refresh_domains:
        latest_risk_score = fetch_latest_risk_score(company_id)
        risk_section = {
            "latest_score": latest_risk_score,
            "top_risk_factors": latest_risk_score.get("top_risk_factors", []) if latest_risk_score else [],
            "priority_actions": [],
        }

    if "alerts" in refresh_domains:
        alerts = fetch_alerts(company_id, limit=10)
        alerts_summary = _summarize_alerts(alerts)
        alerts_section = alerts_summary

    summary_cards = build_summary_cards(
        cashflow_metrics=cashflow_metrics,
        marketing_metrics=marketing_metrics,
        latest_risk_score=latest_risk_score,
        alerts_summary=alerts_summary,
    )

    snapshot_json = {
        "company": {
            "id": company_id,
            "name": company.get("name"),
        },
        "period": {
            "cashflow_days": CASHFLOW_DAYS,
            "marketing_days": MARKETING_DAYS,
        },
        "summary_cards": summary_cards,
        "cashflow": cashflow_section,
        "marketing": marketing_section,
        "risk": risk_section,
        "alerts": alerts_section,
    }

    data_last_seen = {
        "cashflow_data_last_seen_at": get_last_seen_at(company_id, "bank_transactions", "transaction_date"),
        "marketing_data_last_seen_at": get_last_seen_at(company_id, "marketing_campaigns", "campaign_start_at"),
        "risk_score_last_seen_at": get_last_seen_at(company_id, "risk_scores", "score_date"),
        "alerts_last_seen_at": get_last_seen_at(company_id, "alerts", "created_at"),
    }

    return snapshot_json, data_last_seen


def _domains_due_for_refresh(refresh_state: dict) -> set[DomainName]:
    """Domains due for refresh for internal workflow use."""
    domains: set[DomainName] = set()

    if (
        refresh_state.get("cashflow_dirty")
        or int(refresh_state.get("pending_cashflow_events") or 0) >= CASHFLOW_EVENT_THRESHOLD
        or _minutes_since(refresh_state.get("cashflow_last_refreshed_at")) >= CASHFLOW_REFRESH_MINUTES
    ):
        domains.add("cashflow")

    if (
        refresh_state.get("marketing_dirty")
        or int(refresh_state.get("pending_marketing_events") or 0) >= MARKETING_EVENT_THRESHOLD
        or _minutes_since(refresh_state.get("marketing_last_refreshed_at")) >= MARKETING_REFRESH_MINUTES
    ):
        domains.add("marketing")

    if (
        refresh_state.get("risk_dirty")
        or _minutes_since(refresh_state.get("risk_last_refreshed_at")) >= RISK_REFRESH_MINUTES
    ):
        domains.add("risk")

    if (
        refresh_state.get("alerts_dirty")
        or int(refresh_state.get("pending_alert_events") or 0) >= ALERT_EVENT_THRESHOLD
        or _minutes_since(refresh_state.get("alerts_last_refreshed_at")) >= ALERTS_REFRESH_MINUTES
    ):
        domains.add("alerts")

    return domains


def refresh_company_dashboard(
    company_id: str,
    *,
    force_full: bool = False,
    create_daily_history: bool = False,
) -> dict:
    """Refresh company dashboard for the service workflow."""
    refresh_state = get_or_create_refresh_state(company_id)
    latest_snapshot = get_latest_dashboard_snapshot(company_id)

    existing_json = latest_snapshot.get("snapshot_json") if latest_snapshot else None

    if force_full:
        refresh_domains: set[DomainName] = {"cashflow", "marketing", "risk", "alerts"}
    else:
        refresh_domains = _domains_due_for_refresh(refresh_state)

    if not latest_snapshot:
        refresh_domains = {"cashflow", "marketing", "risk", "alerts"}

    if not refresh_domains and latest_snapshot:
        return latest_snapshot

    snapshot_json, last_seen = _build_snapshot_json(
        company_id=company_id,
        existing_snapshot_json=existing_json,
        refresh_domains=refresh_domains,
    )

    now_iso = _now_iso()
    expires_at = (_now() + timedelta(minutes=5)).isoformat()

    cashflow_refreshed_at = now_iso if "cashflow" in refresh_domains else latest_snapshot.get("cashflow_refreshed_at") if latest_snapshot else None
    marketing_refreshed_at = now_iso if "marketing" in refresh_domains else latest_snapshot.get("marketing_refreshed_at") if latest_snapshot else None
    risk_refreshed_at = now_iso if "risk" in refresh_domains else latest_snapshot.get("risk_refreshed_at") if latest_snapshot else None
    alerts_refreshed_at = now_iso if "alerts" in refresh_domains else latest_snapshot.get("alerts_refreshed_at") if latest_snapshot else None

    saved_snapshot = upsert_latest_dashboard_snapshot(
        company_id=company_id,
        snapshot_json=snapshot_json,
        cashflow_data_last_seen_at=last_seen["cashflow_data_last_seen_at"],
        marketing_data_last_seen_at=last_seen["marketing_data_last_seen_at"],
        risk_score_last_seen_at=last_seen["risk_score_last_seen_at"],
        alerts_last_seen_at=last_seen["alerts_last_seen_at"],
        cashflow_refreshed_at=cashflow_refreshed_at,
        marketing_refreshed_at=marketing_refreshed_at,
        risk_refreshed_at=risk_refreshed_at,
        alerts_refreshed_at=alerts_refreshed_at,
        expires_at=expires_at,
        is_stale=False,
    )

    updates = {}

    if "cashflow" in refresh_domains:
        updates.update(
            {
                "cashflow_dirty": False,
                "pending_cashflow_events": 0,
                "cashflow_last_refreshed_at": now_iso,
            }
        )

    if "marketing" in refresh_domains:
        updates.update(
            {
                "marketing_dirty": False,
                "pending_marketing_events": 0,
                "marketing_last_refreshed_at": now_iso,
            }
        )

    if "risk" in refresh_domains:
        updates.update(
            {
                "risk_dirty": False,
                "pending_risk_events": 0,
                "risk_last_refreshed_at": now_iso,
            }
        )

    if "alerts" in refresh_domains:
        updates.update(
            {
                "alerts_dirty": False,
                "pending_alert_events": 0,
                "alerts_last_refreshed_at": now_iso,
            }
        )

    if create_daily_history or _hours_since(refresh_state.get("daily_snapshot_last_created_at")) >= DAILY_SNAPSHOT_HOURS:
        insert_dashboard_snapshot_history(
            company_id=company_id,
            snapshot_json=snapshot_json,
            cashflow_data_last_seen_at=last_seen["cashflow_data_last_seen_at"],
            marketing_data_last_seen_at=last_seen["marketing_data_last_seen_at"],
            risk_score_last_seen_at=last_seen["risk_score_last_seen_at"],
            alerts_last_seen_at=last_seen["alerts_last_seen_at"],
        )
        updates["daily_snapshot_last_created_at"] = now_iso

    if updates:
        update_refresh_state(company_id, updates)

    return saved_snapshot


def refresh_due_dashboards() -> dict:
    """Refresh due dashboards for the service workflow."""
    states = list_refresh_states()
    known_company_ids = {state["company_id"] for state in states}

    for company_id in list_company_ids_from_data():
        if company_id not in known_company_ids:
            get_or_create_refresh_state(company_id)

    refreshed = []
    skipped = []

    for state in list_refresh_states():
        company_id = state["company_id"]
        domains = _domains_due_for_refresh(state)

        should_create_daily = _hours_since(state.get("daily_snapshot_last_created_at")) >= DAILY_SNAPSHOT_HOURS

        if not domains and not should_create_daily:
            skipped.append(company_id)
            continue

        refresh_company_dashboard(
            company_id,
            force_full=False,
            create_daily_history=should_create_daily,
        )
        refreshed.append(company_id)

    return {
        "refreshed_count": len(refreshed),
        "skipped_count": len(skipped),
        "refreshed_company_ids": refreshed,
    }