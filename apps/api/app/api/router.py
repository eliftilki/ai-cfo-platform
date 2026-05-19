from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.ask import router as ask_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.simulation import router as simulations_router


api_router = APIRouter()
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(ask_router, tags=["ask"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(dashboard_router, tags=["dashboard"])
api_router.include_router(simulations_router, tags=["simulations"])
