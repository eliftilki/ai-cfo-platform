## AI CFO Contracts

Shared request and response models live in `packages/contracts/python`.
API service and agent service should import externally visible payload models from
this package instead of redefining them locally.

Current Python contracts:

- `analysis_contracts.py`: `AskRequest`, `AskResponse`, `RunAnalysisRequest`, `RunAnalysisResponse`
- `health_contracts.py`: `HealthResponse`

Keeping these models centralized reduces response-shape drift between services
and gives the frontend a stable source for future TypeScript type generation.
