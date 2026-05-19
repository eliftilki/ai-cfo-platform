from __future__ import annotations

from app.agents.risk_prioritization_engine import risk_prioritization_engine_node


def risk_agent_node(state: dict) -> dict:
    """Risk agent node for the service workflow."""
    return risk_prioritization_engine_node(state)
