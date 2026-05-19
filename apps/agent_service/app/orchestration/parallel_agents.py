from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.agents.cashflow_agent import cashflow_agent_node
from app.agents.marketing_agent import marketing_agent_node


CASHFLOW_STATE_KEYS = {
    "bank_transactions",
    "cashflow_output",
    "cashflow_metrics",
    "cashflow_metrics_presentation",
    "cashflow_flags",
    "latest_cashflow_snapshot",
    "latest_risk_score",
    "cashflow_summary",
    "cashflow_period_context",
    "cashflow_contract",
}

MARKETING_STATE_KEYS = {
    "marketing_output",
    "marketing_metrics",
    "marketing_metrics_presentation",
    "marketing_flags",
    "marketing_summary",
    "marketing_period_context",
    "marketing_contract",
}


def _select_keys(state: dict, keys: set[str]) -> dict:
    """Return only the state fields owned by a parallel domain agent."""
    return {key: state[key] for key in keys if key in state}


def full_chain_parallel_agents_node(state: dict) -> dict:
    """
    Run independent domain agents concurrently for the full-chain workflow.

    Cashflow and marketing do not depend on each other's outputs. Running them
    in parallel keeps the graph faster while preserving a controlled merge
    point before risk prioritization and CFO synthesis.
    """
    branch_state = {
        **state,
        "analysis_mode": "executive_summary",
    }

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="full-chain-agent") as executor:
        cashflow_future = executor.submit(cashflow_agent_node, dict(branch_state))
        marketing_future = executor.submit(marketing_agent_node, dict(branch_state))

        cashflow_result = cashflow_future.result()
        marketing_result = marketing_future.result()

    agent_contracts = {
        **(cashflow_result.get("agent_contracts") or {}),
        **(marketing_result.get("agent_contracts") or {}),
    }

    merged_state = {
        **state,
        **_select_keys(cashflow_result, CASHFLOW_STATE_KEYS),
        **_select_keys(marketing_result, MARKETING_STATE_KEYS),
        "agent_contracts": {
            **(state.get("agent_contracts") or {}),
            **agent_contracts,
        },
        "cashflow_agent_run_id": cashflow_result.get("agent_run_id"),
        "marketing_agent_run_id": marketing_result.get("agent_run_id"),
    }

    return merged_state
