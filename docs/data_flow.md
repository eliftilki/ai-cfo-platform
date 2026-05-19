# Data Flow

1. The user signs in from the web app.
2. The web app sends auth and dashboard requests to Next.js API routes.
3. Next.js proxies those requests to the FastAPI API service.
4. The API service validates the user and company context through Supabase.
5. Dashboard requests read cached snapshots or refresh metrics from source tables.
6. AI CFO chat requests are forwarded to the agent service.
7. The agent service routes the question, computes metrics, calls Gemini when needed and stores the run output.

The frontend reads normalized response shapes from `packages/contracts/python`, mirrored through the API responses.
