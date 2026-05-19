from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.simulation_service import (
    get_company_simulation,
    get_company_simulations,
    run_natural_language_simulation,
    run_structured_simulation,
)
from packages.contracts.python.simulation_contracts import (
    RunNaturalLanguageSimulationRequest,
    RunStructuredSimulationRequest,
    SimulationListItem,
    SimulationResponse,
)


router = APIRouter()


@router.post("/run-structured-simulation", response_model=SimulationResponse)
def run_structured_simulation_endpoint(request: RunStructuredSimulationRequest):
    """Run structured simulation endpoint and return the resulting response."""
    try:
        return run_structured_simulation(
            company_id=request.company_id,
            company_name=request.company_name,
            user_id=request.user_id,
            request=request.simulation,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Structured simulation failed: {str(exc)}")


@router.post("/run-natural-language-simulation", response_model=SimulationResponse)
def run_natural_language_simulation_endpoint(request: RunNaturalLanguageSimulationRequest):
    """Run natural language simulation endpoint and return the resulting response."""
    try:
        return run_natural_language_simulation(
            company_id=request.company_id,
            company_name=request.company_name,
            user_id=request.user_id,
            question=request.question,
            analysis_cashflow_days=request.analysis_cashflow_days,
            analysis_marketing_days=request.analysis_marketing_days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Natural language simulation failed: {str(exc)}")


@router.get("/simulations", response_model=list[SimulationListItem])
def list_simulations_endpoint(
    company_id: str = Query(...),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List simulations endpoint for the requested company or context."""
    try:
        return get_company_simulations(company_id=company_id, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation list failed: {str(exc)}")


@router.get("/simulations/{simulation_id}", response_model=SimulationResponse)
def get_simulation_endpoint(
    simulation_id: str,
    company_id: str = Query(...),
):
    """Return simulation endpoint."""
    try:
        return get_company_simulation(company_id=company_id, simulation_id=simulation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation detail failed: {str(exc)}")