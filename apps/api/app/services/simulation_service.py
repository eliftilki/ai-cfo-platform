from __future__ import annotations

from app.connectors.agent_service_client import agent_service_client
from packages.contracts.python.simulation_contracts import (
    SimulationAskRequest,
    SimulationListItem,
    SimulationRequest,
    SimulationResponse,
)


def run_structured_simulation_flow(
    *,
    company_id: str,
    company_name: str | None,
    user_id: str | None,
    request: SimulationRequest,
) -> SimulationResponse:
    """Run structured simulation flow and return the resulting response."""
    return agent_service_client.run_structured_simulation(
        company_id=company_id,
        company_name=company_name,
        user_id=user_id,
        simulation=request,
    )


def run_natural_language_simulation_flow(
    *,
    company_id: str,
    company_name: str | None,
    user_id: str | None,
    request: SimulationAskRequest,
) -> SimulationResponse:
    """Run natural language simulation flow and return the resulting response."""
    return agent_service_client.run_natural_language_simulation(
        company_id=company_id,
        company_name=company_name,
        user_id=user_id,
        question=request.question,
        analysis_cashflow_days=request.analysis_cashflow_days,
        analysis_marketing_days=request.analysis_marketing_days,
    )


def list_simulations_flow(
    *,
    company_id: str,
    limit: int,
) -> list[SimulationListItem]:
    """List simulations flow for the requested company or context."""
    return agent_service_client.list_simulations(
        company_id=company_id,
        limit=limit,
    )


def get_simulation_flow(
    *,
    company_id: str,
    simulation_id: str,
) -> SimulationResponse:
    """Return simulation flow."""
    return agent_service_client.get_simulation(
        company_id=company_id,
        simulation_id=simulation_id,
    )