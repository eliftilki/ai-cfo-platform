from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.cashflow_agent import cashflow_agent_node
from app.agents.cfo_response_generator import cfo_response_generator_node
from app.agents.marketing_agent import marketing_agent_node
from app.agents.risk_prioritization_engine import risk_prioritization_engine_node
from app.orchestration.intent_router import intent_router_node
from app.orchestration.parallel_agents import full_chain_parallel_agents_node
from app.orchestration.state import AgentState


def route_from_decision(state: AgentState) -> str:
    """Route from decision to the next workflow step."""
    return state.get("route_decision") or "full_chain"


def after_cashflow(state: AgentState) -> str:
    """After cashflow for the service workflow."""
    if state.get("requires_synthesis") or state.get("requires_executive_response"):
        return "marketing_agent"
    return END


def after_marketing(state: AgentState) -> str:
    """After marketing for the service workflow."""
    if state.get("requires_synthesis") or state.get("requires_executive_response"):
        return "risk_prioritization_engine"
    return END


def after_risk(state: AgentState) -> str:
    """After risk for the service workflow."""
    if state.get("requires_executive_response"):
        return "cfo_response_generator"
    return END


def build_analysis_graph():
    """Build analysis graph for downstream service or UI use."""
    graph = StateGraph(AgentState)

    graph.add_node("intent_router", intent_router_node)
    graph.add_node("cashflow_agent", cashflow_agent_node)
    graph.add_node("marketing_agent", marketing_agent_node)
    graph.add_node("full_chain_parallel_agents", full_chain_parallel_agents_node)
    graph.add_node("risk_prioritization_engine", risk_prioritization_engine_node)
    graph.add_node("cfo_response_generator", cfo_response_generator_node)

    graph.add_edge(START, "intent_router")

    graph.add_conditional_edges(
        "intent_router",
        route_from_decision,
        {
            "cashflow_agent": "cashflow_agent",
            "marketing_agent": "marketing_agent",
            "full_chain": "full_chain_parallel_agents",
        },
    )

    graph.add_edge("full_chain_parallel_agents", "risk_prioritization_engine")

    graph.add_conditional_edges(
        "cashflow_agent",
        after_cashflow,
        {
            "marketing_agent": "marketing_agent",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "marketing_agent",
        after_marketing,
        {
            "risk_prioritization_engine": "risk_prioritization_engine",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "risk_prioritization_engine",
        after_risk,
        {
            "cfo_response_generator": "cfo_response_generator",
            END: END,
        },
    )

    graph.add_edge("cfo_response_generator", END)

    return graph.compile()
