from __future__ import annotations

import httpx
from packages.contracts.python.analysis_contracts import (
    RunAnalysisRequest,
    RunAnalysisResponse,
)
from packages.contracts.python.simulation_contracts import (
    RunNaturalLanguageSimulationRequest,
    RunStructuredSimulationRequest,
    SimulationListItem,
    SimulationRequest,
    SimulationResponse,
)

from app.core.config import settings


class AgentServiceError(Exception):
    """Raised when agent service returns an error or is unreachable."""


class AgentServiceClient:
    def __init__(self, base_url: str):
        """Initialize the object with its required runtime configuration."""
        self.base_url = base_url.rstrip("/")

    def run_analysis(
        self,
        company_id: str,
        question: str,
        trigger_type: str = "user_query",
        trigger_reference: str | None = None,
        run_group_id: str | None = None,
        company_name: str | None = None,
    ) -> RunAnalysisResponse:
        """Run analysis and return the resulting response."""
        payload = RunAnalysisRequest(
            company_id=company_id,
            question=question,
            trigger_type=trigger_type,
            trigger_reference=trigger_reference,
            run_group_id=run_group_id,
            company_name=company_name,
        )

        try:
            response = httpx.post(
                f"{self.base_url}/run-analysis",
                json=_model_dump(payload),
                timeout=120.0,
            )
            response.raise_for_status()
            return RunAnalysisResponse(**response.json())

        except httpx.HTTPStatusError as exc:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except ValueError:
                pass

            raise AgentServiceError(f"Agent service failed: {detail}") from exc

        except httpx.RequestError as exc:
            raise AgentServiceError(f"Agent service unreachable: {str(exc)}") from exc

    def health(self) -> dict:
        """Return service health information."""
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise AgentServiceError(f"Agent service health check failed: {str(exc)}") from exc

    def run_structured_simulation(
        self,
        *,
        company_id: str,
        company_name: str | None,
        user_id: str | None,
        simulation: SimulationRequest,
    ) -> SimulationResponse:
        """Run structured simulation and return the resulting response."""
        payload = RunStructuredSimulationRequest(
            company_id=company_id,
            company_name=company_name,
            user_id=user_id,
            simulation=simulation,
        )

        try:
            response = httpx.post(
                f"{self.base_url}/run-structured-simulation",
                json=_model_dump(payload),
                timeout=120.0,
            )
            response.raise_for_status()
            return SimulationResponse(**response.json())

        except httpx.HTTPStatusError as exc:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except ValueError:
                pass

            raise AgentServiceError(f"Agent service simulation failed: {detail}") from exc

        except httpx.RequestError as exc:
            raise AgentServiceError(f"Agent service unreachable: {str(exc)}") from exc

    def run_natural_language_simulation(
        self,
        *,
        company_id: str,
        company_name: str | None,
        user_id: str | None,
        question: str,
        analysis_cashflow_days: int = 30,
        analysis_marketing_days: int = 60,
    ) -> SimulationResponse:
        """Run natural language simulation and return the resulting response."""
        payload = RunNaturalLanguageSimulationRequest(
            company_id=company_id,
            company_name=company_name,
            user_id=user_id,
            question=question,
            analysis_cashflow_days=analysis_cashflow_days,
            analysis_marketing_days=analysis_marketing_days,
        )

        try:
            response = httpx.post(
                f"{self.base_url}/run-natural-language-simulation",
                json=_model_dump(payload),
                timeout=120.0,
            )
            response.raise_for_status()
            return SimulationResponse(**response.json())

        except httpx.HTTPStatusError as exc:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except ValueError:
                pass

            raise AgentServiceError(f"Agent service simulation failed: {detail}") from exc

        except httpx.RequestError as exc:
            raise AgentServiceError(f"Agent service unreachable: {str(exc)}") from exc

    def list_simulations(
        self,
        *,
        company_id: str,
        limit: int = 20,
    ) -> list[SimulationListItem]:
        """List simulations for the requested company or context."""
        try:
            response = httpx.get(
                f"{self.base_url}/simulations",
                params={"company_id": company_id, "limit": limit},
                timeout=30.0,
            )
            response.raise_for_status()
            return [SimulationListItem(**item) for item in response.json()]

        except httpx.HTTPStatusError as exc:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except ValueError:
                pass

            raise AgentServiceError(f"Agent service simulation list failed: {detail}") from exc

        except httpx.RequestError as exc:
            raise AgentServiceError(f"Agent service unreachable: {str(exc)}") from exc

    def get_simulation(
        self,
        *,
        company_id: str,
        simulation_id: str,
    ) -> SimulationResponse:
        """Return simulation."""
        try:
            response = httpx.get(
                f"{self.base_url}/simulations/{simulation_id}",
                params={"company_id": company_id},
                timeout=30.0,
            )
            response.raise_for_status()
            return SimulationResponse(**response.json())

        except httpx.HTTPStatusError as exc:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except ValueError:
                pass

            raise AgentServiceError(f"Agent service simulation detail failed: {detail}") from exc

        except httpx.RequestError as exc:
            raise AgentServiceError(f"Agent service unreachable: {str(exc)}") from exc


agent_service_client = AgentServiceClient(settings.agent_service_base_url)


def _model_dump(model) -> dict:
    """Serialize a Pydantic model across supported Pydantic versions."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
