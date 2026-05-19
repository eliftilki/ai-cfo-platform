from __future__ import annotations

import unittest

from app.agents.output_contracts import build_agent_output_contract


class AgentOutputContractTests(unittest.TestCase):
    def test_contract_contains_required_common_fields(self):
        """Verify every normalized agent contract exposes the required envelope fields."""
        contract = build_agent_output_contract(
            agent_name="cashflow_agent",
            metrics={"net_cashflow_30d": 100},
            flags=["positive_cashflow"],
            summary="Cashflow is healthy.",
            confidence=1.2,
            data_coverage={"row_count": 10},
            errors=[],
        )

        payload = contract.dict()

        self.assertEqual(
            set(payload.keys()),
            {
                "agent_name",
                "metrics",
                "flags",
                "summary",
                "confidence",
                "data_coverage",
                "errors",
            },
        )
        self.assertEqual(payload["confidence"], 1.0)


if __name__ == "__main__":
    unittest.main()
