from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.run_analysis import router as run_analysis_router
from app.api.routes.run_simulation import router as simulation_router

api_router = APIRouter()
api_router.include_router(run_analysis_router, tags=["analysis"])
api_router.include_router(simulation_router)