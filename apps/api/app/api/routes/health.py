from __future__ import annotations

from fastapi import APIRouter
from packages.contracts.python.health_contracts import HealthResponse

from app.services.health_service import get_health_status


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    """Return service health information."""
    return get_health_status()
