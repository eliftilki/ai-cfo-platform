from __future__ import annotations

import unittest

from app.orchestration.intent_router import (
    IntentDecision,
    _coerce_decision,
    _deterministic_example_decision,
    _extract_json_object,
    route_decision_from_intent,
)


class IntentRouterTests(unittest.TestCase):
    def test_cashflow_example_routes_to_cashflow_only(self):
        """Test cashflow example routes to cashflow only for the service workflow."""
        decision = _deterministic_example_decision("Şirketimin nakit durumu nasıl?")

        self.assertIsNotNone(decision)
        self.assertEqual(decision.intent, "cashflow_query")
        self.assertEqual(decision.required_agents, ["cashflow"])
        self.assertFalse(decision.requires_synthesis)
        self.assertEqual(route_decision_from_intent(decision), "cashflow_agent")

    def test_marketing_example_routes_to_marketing_only(self):
        """Test marketing example routes to marketing only for the service workflow."""
        decision = _deterministic_example_decision("ROAS nasıl?")

        self.assertIsNotNone(decision)
        self.assertEqual(decision.intent, "marketing_query")
        self.assertEqual(decision.required_agents, ["marketing"])
        self.assertFalse(decision.requires_executive_response)
        self.assertEqual(route_decision_from_intent(decision), "marketing_agent")

    def test_multi_domain_example_routes_to_full_chain(self):
        """Test multi domain example routes to full chain for the service workflow."""
        decision = _deterministic_example_decision("Nakit ve reklam tarafında sorun var mı?")

        self.assertIsNotNone(decision)
        self.assertEqual(decision.intent, "general_finance_query")
        self.assertEqual(decision.required_agents, ["cashflow", "marketing"])
        self.assertTrue(decision.requires_synthesis)
        self.assertTrue(decision.requires_executive_response)
        self.assertEqual(route_decision_from_intent(decision), "full_chain")

    def test_low_confidence_decision_falls_back_to_full_chain(self):
        """Test low confidence decision falls back to full chain for the service workflow."""
        decision = IntentDecision(
            intent="cashflow_query",
            required_agents=["cashflow"],
            requires_synthesis=False,
            requires_executive_response=False,
            confidence=0.2,
            reason="Ambiguous wording.",
        )

        coerced = _coerce_decision(decision)

        self.assertEqual(coerced.intent, "unknown")
        self.assertEqual(coerced.required_agents, ["cashflow", "marketing"])
        self.assertTrue(coerced.requires_synthesis)
        self.assertEqual(route_decision_from_intent(coerced), "full_chain")

    def test_extract_json_object_from_wrapped_llm_text(self):
        """Test extract json object from wrapped llm text for the service workflow."""
        payload = _extract_json_object(
            'Here is the result: {"intent": "marketing_query", "required_agents": ["marketing"], '
            '"requires_synthesis": false, "requires_executive_response": false, '
            '"confidence": 0.9, "reason": "ROAS question"}'
        )

        self.assertEqual(payload["intent"], "marketing_query")
        self.assertEqual(payload["required_agents"], ["marketing"])


if __name__ == "__main__":
    unittest.main()
