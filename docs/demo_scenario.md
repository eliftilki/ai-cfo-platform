# Demo Scenario

Recommended demo path for judges:

1. Start the agent service on port `8001`.
2. Start the API service on port `8000`.
3. Start the web app on port `3000`.
4. Sign in with a seeded Supabase user that has an active `user_company_memberships` record.
5. Open `/dashboard` and show cashflow, marketing and risk summary cards.
6. Open `/text-generator` and ask:

```text
Son 30 gunde nakit akisim nasil ve en acil 3 aksiyonum ne?
```

7. Run a simulation prompt:

```text
Reklam butcesini yuzde 20 azaltirsam nakit akisim nasil etkilenir?
```
