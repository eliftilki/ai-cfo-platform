from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps.auth import get_current_user_context
from app.services.dashboard_service import get_dashboard_overview
from packages.contracts.python.auth_contracts import MeResponse
from packages.contracts.python.dashboard_contracts import DashboardOverviewResponse


router = APIRouter()


@router.get("/dashboard/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(
    current_user: MeResponse = Depends(get_current_user_context),
):
    """Dashboard overview for the service workflow."""
    try:
        return get_dashboard_overview(company_id=current_user.company_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Dashboard overview failed: {str(exc)}")