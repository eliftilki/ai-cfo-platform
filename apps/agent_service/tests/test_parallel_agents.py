from __future__ import annotations

import time
import unittest
from unittest.mock import patch

from app.orchestration.parallel_agents import full_chain_parallel_agents_node


class FullChainParallelAgentsTests(unittest.TestCase):
    def test_full_chain_runs_cashflow_and_marketing_concurrently(self):
        """Verify full-chain domain agents run in parallel and merge owned state fields."""

        def fake_cashflow_agent(state: dict) -> dict:
            """Return a fake cashflow branch result after a short delay."""
            time.sleep(0.2)
            return {
                **state,
                "cashflow_metrics": {"net_cashflow_30d": 100},
                "cashflow_flags": ["positive_cashflow"],
                "cashflow_contract": {
                    "agent_name": "cashflow_agent",
                    "metrics": {"net_cashflow_30d": 100},
                    "flags": ["positive_cashflow"],
                    "summary": None,
                    "confidence": 0.92,
                    "data_coverage": {},
                    "errors": [],
                },
                "agent_contracts": {
                    "cashflow_agent": {
                        "agent_name": "cashflow_agent",
                        "metrics": {"net_cashflow_30d": 100},
                        "flags": ["positive_cashflow"],
                        "summary": None,
                        "confidence": 0.92,
                        "data_coverage": {},
                        "errors": [],
                    }
                },
                "cashflow_agent_only": "ignored",
                "agent_run_id": "cashflow-run",
            }

        def fake_marketing_agent(state: dict) -> dict:
            """Return a fake marketing branch result after a short delay."""
            time.sleep(0.2)
            return {
                **state,
                "marketing_metrics": {"overall_roas": 2.4},
                "marketing_flags": ["healthy_roas"],
                "marketing_contract": {
                    "agent_name": "marketing_agent",
                    "metrics": {"overall_roas": 2.4},
                    "flags": ["healthy_roas"],
                    "summary": None,
                    "confidence": 0.91,
                    "data_coverage": {},
                    "errors": [],
                },
                "agent_contracts": {
                    "marketing_agent": {
                        "agent_name": "marketing_agent",
                        "metrics": {"overall_roas": 2.4},
                        "flags": ["healthy_roas"],
                        "summary": None,
                        "confidence": 0.91,
                        "data_coverage": {},
                        "errors": [],
                    }
                },
                "marketing_agent_only": "ignored",
                "agent_run_id": "marketing-run",
            }

        state = {
            "company_id": "company-1",
            "user_question": "Genel finansal durumum nasil?",
            "analysis_mode": "executive_summary",
        }

        started_at = time.perf_counter()
        with patch(
            "app.orchestration.parallel_agents.cashflow_agent_node",
            side_effect=fake_cashflow_agent,
        ), patch(
            "app.orchestration.parallel_agents.marketing_agent_node",
            side_effect=fake_marketing_agent,
        ):
            result = full_chain_parallel_agents_node(state)
        elapsed = time.perf_counter() - started_at

        self.assertLess(elapsed, 0.35)
        self.assertEqual(result["cashflow_metrics"], {"net_cashflow_30d": 100})
        self.assertEqual(result["marketing_metrics"], {"overall_roas": 2.4})
        self.assertEqual(result["cashflow_agent_run_id"], "cashflow-run")
        self.assertEqual(result["marketing_agent_run_id"], "marketing-run")
        self.assertEqual(
            set(result["agent_contracts"].keys()),
            {"cashflow_agent", "marketing_agent"},
        )
        self.assertNotIn("cashflow_agent_only", result)
        self.assertNotIn("marketing_agent_only", result)


if __name__ == "__main__":
    unittest.main()
