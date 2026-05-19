from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    agent_service: dict[str, Any] | None = None
