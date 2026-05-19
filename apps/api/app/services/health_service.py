from __future__ import annotations

from app.connectors.agent_service_client import agent_service_client
from app.core.config import settings


def get_health_status() -> dict:
    """Return health status."""
    agent_health = None
    try:
        agent_health = agent_service_client.health()
    except Exception as exc:
        agent_health = {
            "status": "unreachable",
            "detail": str(exc),
        }

    return {
        "status": "ok",
        "service": "api_service",
        "environment": settings.app_env,
        "agent_service": agent_health,
    }