from __future__ import annotations

from app.agents.cfo_response_generator import cfo_response_generator_node


def cfo_agent_node(state: dict) -> dict:
    """Cfo agent node for the service workflow."""
    return cfo_response_generator_node(state)
