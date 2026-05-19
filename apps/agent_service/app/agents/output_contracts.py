from __future__ import annotations

from typing import Any

from app.schemas.agent_outputs import AgentOutputContract


def build_agent_output_contract(
    *,
    agent_name: str,
    metrics: dict[str, Any] | None = None,
    flags: list[str] | None = None,
    summary: str | None = None,
    confidence: float = 0.0,
    data_coverage: dict[str, Any] | None = None,
    errors: list[str] | None = None,
) -> AgentOutputContract:
    """Build the normalized output envelope shared by every agent."""
    return AgentOutputContract(
        agent_name=agent_name,
        metrics=metrics or {},
        flags=flags or [],
        summary=summary,
        confidence=max(0.0, min(1.0, confidence)),
        data_coverage=data_coverage or {},
        errors=errors or [],
    )


def agent_confidence(*, has_data: bool, base: float, empty_data_score: float = 0.55) -> float:
    """Return a conservative confidence score based on data availability."""
    return base if has_data else empty_data_score


def merge_agent_contracts(state: dict, *contracts: AgentOutputContract) -> dict:
    """Merge normalized agent contracts into the workflow state."""
    merged = dict(state.get("agent_contracts") or {})
    for contract in contracts:
        merged[contract.agent_name] = contract.dict()
    return merged
