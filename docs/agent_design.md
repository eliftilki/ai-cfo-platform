# Agent Design

The agent service focuses on CFO-style financial reasoning for small businesses.

Core modules:

- `orchestration/intent_router.py`: classifies the user's question.
- `orchestration/graph.py`: coordinates the analysis graph.
- `orchestration/parallel_agents.py`: runs independent cashflow and marketing branches concurrently in full-chain mode.
- `agents/cashflow_agent.py`: cashflow interpretation.
- `agents/marketing_agent.py`: marketing performance interpretation.
- `agents/risk_prioritization_engine.py`: converts signals into action priorities.
- `agents/cfo_response_generator.py`: produces the final executive answer.
- `agents/simulation_agent.py`: handles structured and natural-language scenario simulations.

The preferred fallback for low-confidence routing is a broader analysis chain so the user receives a useful CFO-level response instead of a narrow answer.

In full-chain mode, cashflow and marketing agents run in parallel because they read independent data domains. Their outputs are merged through a controlled state boundary before risk prioritization and CFO response generation.

## Output Contract

Every agent emits a normalized contract alongside its domain-specific fields:

```text
metrics
flags
summary
confidence
data_coverage
errors
```

The domain-specific fields remain available for backward compatibility, while the normalized contract gives the risk and CFO layers a consistent structure for synthesis, partial-failure handling and response rendering.
