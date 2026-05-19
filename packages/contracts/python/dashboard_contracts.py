from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


DashboardRefreshStatus = Literal[
    "fresh",
    "stale",
    "generated_on_demand",
    "missing",
]


class DashboardCompany(BaseModel):
    id: str
    name: str | None = None


class DashboardPeriod(BaseModel):
    cashflow_days: int = 30
    marketing_days: int = 60


class DashboardDataFreshness(BaseModel):
    cashflow_data_last_seen_at: str | None = None
    marketing_data_last_seen_at: str | None = None
    risk_score_last_seen_at: str | None = None
    alerts_last_seen_at: str | None = None

    cashflow_refreshed_at: str | None = None
    marketing_refreshed_at: str | None = None
    risk_refreshed_at: str | None = None
    alerts_refreshed_at: str | None = None


class DashboardOverviewResponse(BaseModel):
    company: DashboardCompany
    period: DashboardPeriod
    refresh_status: DashboardRefreshStatus
    generated_at: str | None = None
    expires_at: str | None = None
    is_stale: bool = False
    data_freshness: DashboardDataFreshness

    summary_cards: dict[str, Any] = Field(default_factory=dict)
    cashflow: dict[str, Any] = Field(default_factory=dict)
    marketing: dict[str, Any] = Field(default_factory=dict)
    risk: dict[str, Any] = Field(default_factory=dict)
    alerts: dict[str, Any] = Field(default_factory=dict)