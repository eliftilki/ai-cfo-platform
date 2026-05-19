from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps.auth import get_current_user_context
from app.connectors.agent_service_client import AgentServiceError
from app.services.simulation_service import (
    get_simulation_flow,
    list_simulations_flow,
    run_natural_language_simulation_flow,
    run_structured_simulation_flow,
)
from packages.contracts.python.auth_contracts import MeResponse
from packages.contracts.python.simulation_contracts import (
    SimulationAskRequest,
    SimulationListItem,
    SimulationRequest,
    SimulationResponse,
)


router = APIRouter()


@router.post("/simulations/run", response_model=SimulationResponse)
def run_structured_simulation_endpoint(
    request: SimulationRequest,
    current_user: MeResponse = Depends(get_current_user_context),
):
    """Run structured simulation endpoint and return the resulting response."""
    try:
        return run_structured_simulation_flow(
            company_id=current_user.company_id,
            company_name=current_user.company_name,
            user_id=current_user.user_id,
            request=request,
        )
    except AgentServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(exc)}")


@router.post("/simulations/ask", response_model=SimulationResponse)
def ask_simulation_endpoint(
    request: SimulationAskRequest,
    current_user: MeResponse = Depends(get_current_user_context),
):
    """Handle ask simulation endpoint requests from the web app."""
    try:
        return run_natural_language_simulation_flow(
            company_id=current_user.company_id,
            company_name=current_user.company_name,
            user_id=current_user.user_id,
            request=request,
        )
    except AgentServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation agent failed: {str(exc)}")


@router.get("/simulations", response_model=list[SimulationListItem])
def list_simulations_endpoint(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: MeResponse = Depends(get_current_user_context),
):
    """List simulations endpoint for the requested company or context."""
    try:
        return list_simulations_flow(
            company_id=current_user.company_id,
            limit=limit,
        )
    except AgentServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation list failed: {str(exc)}")


@router.get("/simulations/{simulation_id}", response_model=SimulationResponse)
def get_simulation_endpoint(
    simulation_id: str,
    current_user: MeResponse = Depends(get_current_user_context),
):
    """Return simulation endpoint."""
    try:
        return get_simulation_flow(
            company_id=current_user.company_id,
            simulation_id=simulation_id,
        )
    except AgentServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation detail failed: {str(exc)}")