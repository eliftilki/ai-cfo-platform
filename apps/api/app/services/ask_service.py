from __future__ import annotations

import uuid

from packages.contracts.python.analysis_contracts import AskResponse

from app.connectors.agent_service_client import agent_service_client
from app.repositories.auth_repository import get_company_by_id


def run_ask_flow(*, company_id: str, question: str) -> AskResponse:
    """Run ask flow and return the resulting response."""
    company = get_company_by_id(company_id)
    if not company:
        raise ValueError(f"Company not found in AI CFO DB: {company_id}")

    run_group_id = str(uuid.uuid4())

    agent_result = agent_service_client.run_analysis(
        company_id=company_id,
        question=question,
        trigger_type="user_query",
        trigger_reference="api_ask",
        run_group_id=run_group_id,
        company_name=company.get("name"),
    )

    return AskResponse(
        company_id=agent_result.company_id,
        company_name=agent_result.company_name or company.get("name"),
        analysis_type=agent_result.analysis_type,
        selected_agents=agent_result.selected_agents,
        final_response=agent_result.final_response,
        sections=agent_result.sections,
        agent_run_id=agent_result.agent_run_id,
    )