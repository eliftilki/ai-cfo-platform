# Database Design

The MVP assumes two Supabase projects or schemas:

- `kobiDB`: operational source data such as transactions, invoices, campaigns and external feeds.
- `AI_CFO`: application data, normalized analytics data, dashboard snapshots and agent outputs.

Important AI_CFO table groups:

- Identity: `companies`, `user_profiles`, `user_company_memberships`
- Finance and operations: `bank_transactions`, `marketing_campaigns`, `expense_invoices`
- Analytics: `cashflow_snapshots`, `risk_scores`, `alerts`, `dashboard_snapshot_latest`
- AI workflow: `agent_runs`, `agent_outputs`, `simulations`, `decisions`

SQL migration placeholders live in `infrastructure/sql` so the prototype schema can be promoted into repeatable migrations later.
