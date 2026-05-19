import os
import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()

SOURCE_SUPABASE_URL = os.getenv("SOURCE_SUPABASE_URL")
SOURCE_SUPABASE_SERVICE_ROLE_KEY = os.getenv("SOURCE_SUPABASE_SERVICE_ROLE_KEY")
AI_CFO_SUPABASE_URL = os.getenv("AI_CFO_SUPABASE_URL")
AI_CFO_SUPABASE_SERVICE_ROLE_KEY = os.getenv("AI_CFO_SUPABASE_SERVICE_ROLE_KEY")

if not all([
    SOURCE_SUPABASE_URL,
    SOURCE_SUPABASE_SERVICE_ROLE_KEY,
    AI_CFO_SUPABASE_URL,
    AI_CFO_SUPABASE_SERVICE_ROLE_KEY,
]):
    raise ValueError("Tüm source ve ai_cfo supabase env değerleri gerekli.")

source_db: Client = create_client(SOURCE_SUPABASE_URL, SOURCE_SUPABASE_SERVICE_ROLE_KEY)
ai_cfo_db: Client = create_client(AI_CFO_SUPABASE_URL, AI_CFO_SUPABASE_SERVICE_ROLE_KEY)

UTC = timezone.utc
BATCH_SIZE = 500


def gen_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def q(val) -> Decimal:
    """Convert a raw numeric value into a Decimal."""
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def now_iso() -> str:
    """Return the current UTC timestamp as an ISO string."""
    return datetime.now(UTC).isoformat()


def parse_dt(value: str | None):
    """Parse an ISO timestamp into a datetime when possible."""
    if value is None:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)


def chunked(seq, size):
    """Yield fixed-size chunks from a sequence."""
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def fetch_all(client: Client, table_name: str, filters: list[tuple] | None = None, columns="*") -> list[dict]:
    """Fetch all matching Supabase rows with pagination."""
    rows = []
    start = 0
    page = 1000
    while True:
        query = client.table(table_name).select(columns).range(start, start + page - 1)
        if filters:
            for f in filters:
                op, col, val = f
                if op == "eq":
                    query = query.eq(col, val)
                elif op == "in":
                    query = query.in_(col, val)
        resp = query.execute()
        data = resp.data or []
        rows.extend(data)
        if len(data) < page:
            break
        start += page
    return rows


def insert_rows(client: Client, table_name: str, rows: list[dict]):
    """Insert rows into a Supabase table in batches."""
    if not rows:
        print(f"[SKIP] {table_name}: 0")
        return
    for batch in chunked(rows, BATCH_SIZE):
        client.table(table_name).insert(batch).execute()
    print(f"[INSERT] {table_name}: {len(rows)}")


def update_rows(client: Client, table_name: str, ids: list[str], payload: dict):
    """Update selected Supabase rows with the provided payload."""
    if not ids:
        return
    for batch in chunked(ids, BATCH_SIZE):
        client.table(table_name).update(payload).in_("id", batch).execute()
    print(f"[UPDATE] {table_name}: {len(ids)}")


def fetch_existing_keys(client: Client, table_name: str, key_field: str) -> set[str]:
    """Fetch existing key values from a Supabase table."""
    rows = fetch_all(client, table_name, columns=key_field)
    return {str(r[key_field]) for r in rows if r.get(key_field) is not None}


# =========================================================
# NORMALIZATION: RAW -> CORE
# =========================================================
def normalize_marketing_events():
    """Normalize marketing events into the platform data model."""
    raw_rows = fetch_all(source_db, "raw_marketing_events", filters=[("eq", "is_processed", False)])
    existing = fetch_existing_keys(ai_cfo_db, "marketing_campaigns", "external_campaign_id")

    to_insert = []
    processed_ids = []

    for row in raw_rows:
        payload = row["payload"]
        external_campaign_id = str(payload["campaign_id"])
        if external_campaign_id in existing:
            processed_ids.append(row["id"])
            continue

        to_insert.append({
            "id": gen_uuid(),
            "company_id": row["company_id"],
            "external_campaign_id": external_campaign_id,
            "campaign_name": payload["campaign_name"],
            "platform": payload["platform"],
            "target_category": payload.get("target_category"),
            "campaign_start_at": payload.get("start_date"),
            "campaign_end_at": payload.get("end_date"),
            "ad_spend": float(q(payload.get("ad_spend", 0))),
            "impressions": int(payload.get("impressions", 0)),
            "clicks": int(payload.get("clicks", 0)),
            "conversions": int(payload.get("conversions", 0)),
            "attributed_orders": int(payload.get("attributed_orders", 0)),
            "attributed_revenue": float(q(payload.get("attributed_revenue", 0))),
            "roas": float(Decimal(str(payload.get("roas", 0)))),
            "cac": float(q(payload.get("cac", 0))),
            "status": payload.get("status"),
            "raw_event_id": row["id"],
            "created_at": now_iso(),
            "updated_at": now_iso(),
        })
        processed_ids.append(row["id"])

    insert_rows(ai_cfo_db, "marketing_campaigns", to_insert)
    update_rows(source_db, "raw_marketing_events", processed_ids, {
        "is_processed": True,
        "processed_at": now_iso(),
    })


def normalize_expense_invoice_events():
    """Normalize expense invoice events into the platform data model."""
    raw_rows = fetch_all(source_db, "raw_expense_invoice_events", filters=[("eq", "is_processed", False)])
    existing = fetch_existing_keys(ai_cfo_db, "expense_invoices", "external_invoice_id")

    to_insert = []
    processed_ids = []

    for row in raw_rows:
        payload = row["payload"]
        external_invoice_id = row["external_event_id"]

        if external_invoice_id in existing:
            processed_ids.append(row["id"])
            continue

        to_insert.append({
            "id": gen_uuid(),
            "company_id": row["company_id"],
            "external_invoice_id": external_invoice_id,
            "invoice_number": payload["invoice_number"],
            "invoice_type": payload["invoice_type"],
            "vendor_name": payload["vendor_name"],
            "vendor_category": payload.get("vendor_category"),
            "invoice_date": payload["invoice_date"],
            "due_date": payload.get("due_date"),
            "subtotal": float(q(payload.get("subtotal", 0))),
            "tax_amount": float(q(payload.get("tax_amount", 0))),
            "total_amount": float(q(payload.get("total_amount", 0))),
            "currency_code": payload.get("currency", "TRY"),
            "payment_status": payload.get("payment_status"),
            "related_purchase_order_number": payload.get("related_purchase_order_number"),
            "related_campaign_id": payload.get("related_campaign_id"),
            "related_campaign_name": payload.get("related_campaign_name"),
            "raw_event_id": row["id"],
            "created_at": now_iso(),
            "updated_at": now_iso(),
        })
        processed_ids.append(row["id"])

    insert_rows(ai_cfo_db, "expense_invoices", to_insert)
    update_rows(source_db, "raw_expense_invoice_events", processed_ids, {
        "is_processed": True,
        "processed_at": now_iso(),
    })


def normalize_bank_events():
    """Normalize bank events into the platform data model."""
    raw_rows = fetch_all(source_db, "raw_bank_events", filters=[("eq", "is_processed", False)])
    existing = fetch_existing_keys(ai_cfo_db, "bank_transactions", "external_transaction_id")

    to_insert = []
    processed_ids = []

    for row in raw_rows:
        payload = row["payload"]
        external_tx_id = str(payload["transaction_id"])

        if external_tx_id in existing:
            processed_ids.append(row["id"])
            continue

        to_insert.append({
            "id": gen_uuid(),
            "company_id": row["company_id"],
            "external_transaction_id": external_tx_id,
            "transaction_date": payload["transaction_date"],
            "amount": float(q(payload.get("amount", 0))),
            "currency_code": payload.get("currency", "TRY"),
            "direction": payload["direction"],
            "description": payload.get("description"),
            "merchant_name": payload.get("merchant_name"),
            "category": payload.get("category"),
            "source_entity_type": payload.get("source_entity_type"),
            "source_entity_ref": payload.get("source_entity_ref"),
            "gross_paid": float(q(payload["gross_paid"])) if payload.get("gross_paid") is not None else None,
            "commission_rate": float(Decimal(str(payload["commission_rate"]))) if payload.get("commission_rate") is not None else None,
            "raw_event_id": row["id"],
            "created_at": now_iso(),
            "updated_at": now_iso(),
        })
        processed_ids.append(row["id"])

    insert_rows(ai_cfo_db, "bank_transactions", to_insert)
    update_rows(source_db, "raw_bank_events", processed_ids, {
        "is_processed": True,
        "processed_at": now_iso(),
    })


def normalize_macro_events():
    """Normalize macro events into the platform data model."""
    raw_rows = fetch_all(source_db, "raw_macro_events", filters=[("eq", "is_processed", False)])
    existing = fetch_existing_keys(ai_cfo_db, "macro_market_data", "external_metric_id")

    to_insert = []
    processed_ids = []

    for row in raw_rows:
        payload = row["payload"]
        external_metric_id = row["external_event_id"]

        if external_metric_id in existing:
            processed_ids.append(row["id"])
            continue

        to_insert.append({
            "id": gen_uuid(),
            "company_id": row["company_id"],
            "external_metric_id": external_metric_id,
            "metric_name": payload["metric_name"],
            "metric_value": float(Decimal(str(payload["metric_value"]))),
            "metric_unit": payload.get("metric_unit"),
            "captured_at": payload["captured_at"],
            "source": payload.get("source"),
            "raw_event_id": row["id"],
            "created_at": now_iso(),
            "updated_at": now_iso(),
        })
        processed_ids.append(row["id"])

    insert_rows(ai_cfo_db, "macro_market_data", to_insert)
    update_rows(source_db, "raw_macro_events", processed_ids, {
        "is_processed": True,
        "processed_at": now_iso(),
    })


# =========================================================
# LINKING
# =========================================================
def generate_transaction_links():
    """Generate transaction links for the AI CFO workflow."""
    campaigns = fetch_all(ai_cfo_db, "marketing_campaigns", columns="id, external_campaign_id, company_id")
    invoices = fetch_all(ai_cfo_db, "expense_invoices", columns="id, invoice_number, company_id")
    bank_transactions = fetch_all(
        ai_cfo_db,
        "bank_transactions",
        columns="id, company_id, external_transaction_id, source_entity_type, source_entity_ref"
    )
    existing_links = fetch_all(
        ai_cfo_db,
        "transaction_links",
        columns="bank_transaction_id, linked_entity_type, linked_entity_id"
    )

    existing_set = {(x["bank_transaction_id"], x["linked_entity_type"], x["linked_entity_id"]) for x in existing_links}
    campaign_map = {c["external_campaign_id"]: c for c in campaigns}
    invoice_map = {i["invoice_number"]: i for i in invoices}

    to_insert = []

    for tx in bank_transactions:
        linked_type = tx.get("source_entity_type")
        linked_ref = tx.get("source_entity_ref")
        bank_tx_id = tx["id"]

        if linked_type == "marketing_campaign":
            campaign = campaign_map.get(linked_ref)
            if campaign:
                key = (bank_tx_id, "marketing_campaign", campaign["id"])
                if key not in existing_set:
                    to_insert.append({
                        "id": gen_uuid(),
                        "company_id": tx["company_id"],
                        "bank_transaction_id": bank_tx_id,
                        "linked_entity_type": "marketing_campaign",
                        "linked_entity_id": campaign["id"],
                        "match_method": "source_entity_ref",
                        "confidence_score": 0.99,
                        "created_at": now_iso(),
                    })

        elif linked_type == "expense_invoice":
            invoice = invoice_map.get(linked_ref)
            if invoice:
                key = (bank_tx_id, "expense_invoice", invoice["id"])
                if key not in existing_set:
                    to_insert.append({
                        "id": gen_uuid(),
                        "company_id": tx["company_id"],
                        "bank_transaction_id": bank_tx_id,
                        "linked_entity_type": "expense_invoice",
                        "linked_entity_id": invoice["id"],
                        "match_method": "source_entity_ref",
                        "confidence_score": 0.99,
                        "created_at": now_iso(),
                    })

    insert_rows(ai_cfo_db, "transaction_links", to_insert)


# =========================================================
# ANALYTICS
# =========================================================
def compute_cashflow_snapshots():
    """Compute cashflow snapshots from normalized input data."""
    companies = fetch_all(ai_cfo_db, "bank_transactions", columns="company_id")
    company_ids = sorted(list({x["company_id"] for x in companies}))
    now = datetime.now(UTC)

    existing_today = fetch_all(
        ai_cfo_db,
        "cashflow_snapshots",
        columns="company_id, snapshot_date"
    )
    existing_keys = {
        (x["company_id"], parse_dt(x["snapshot_date"]).date().isoformat())
        for x in existing_today
    }

    to_insert = []

    for company_id in company_ids:
        rows = fetch_all(ai_cfo_db, "bank_transactions", filters=[("eq", "company_id", company_id)])
        if not rows:
            continue

        key = (company_id, now.date().isoformat())
        if key in existing_keys:
            continue

        income_7 = Decimal("0")
        expense_7 = Decimal("0")
        income_30 = Decimal("0")
        expense_30 = Decimal("0")

        last_7 = now - timedelta(days=7)
        last_30 = now - timedelta(days=30)

        for tx in rows:
            dt = parse_dt(tx["transaction_date"])
            amount = Decimal(str(tx["amount"]))
            direction = tx["direction"]

            if dt >= last_30:
                if direction == "income":
                    income_30 += amount
                else:
                    expense_30 += amount

            if dt >= last_7:
                if direction == "income":
                    income_7 += amount
                else:
                    expense_7 += amount

        net_30 = income_30 - expense_30
        net_7 = income_7 - expense_7

        if net_30 > Decimal("50000"):
            risk = "low"
        elif net_30 > Decimal("0"):
            risk = "medium"
        elif net_30 > Decimal("-50000"):
            risk = "high"
        else:
            risk = "critical"

        to_insert.append({
            "id": gen_uuid(),
            "company_id": company_id,
            "snapshot_date": now_iso(),
            "income_7d": float(q(income_7)),
            "expense_7d": float(q(expense_7)),
            "net_cashflow_7d": float(q(net_7)),
            "income_30d": float(q(income_30)),
            "expense_30d": float(q(expense_30)),
            "net_cashflow_30d": float(q(net_30)),
            "liquidity_risk": risk,
            "summary": f"30d net cashflow: {float(q(net_30))}, liquidity risk: {risk}",
            "created_at": now_iso(),
        })

    insert_rows(ai_cfo_db, "cashflow_snapshots", to_insert)


def compute_risk_scores():
    """Compute risk scores from normalized input data."""
    snapshots = fetch_all(ai_cfo_db, "cashflow_snapshots")
    marketing = fetch_all(ai_cfo_db, "marketing_campaigns")
    macros = fetch_all(ai_cfo_db, "macro_market_data")

    if not snapshots:
        print("[SKIP] risk_scores: no cashflow snapshots")
        return

    latest_snapshot_by_company = {}
    for s in sorted(snapshots, key=lambda x: x["snapshot_date"]):
        latest_snapshot_by_company[s["company_id"]] = s

    existing_today = fetch_all(ai_cfo_db, "risk_scores", columns="company_id, score_date")
    existing_keys = {
        (x["company_id"], parse_dt(x["score_date"]).date().isoformat())
        for x in existing_today
    }

    to_insert = []
    now = datetime.now(UTC)

    for company_id, snap in latest_snapshot_by_company.items():
        key = (company_id, now.date().isoformat())
        if key in existing_keys:
            continue

        cashflow_component = 0
        marketing_component = 0
        inventory_component = 10
        tax_component = 10
        macro_component = 0
        top_risk_factors = []

        net_30 = Decimal(str(snap["net_cashflow_30d"]))
        if net_30 > Decimal("50000"):
            cashflow_component = 10
        elif net_30 > Decimal("0"):
            cashflow_component = 25
            top_risk_factors.append("weakening_cashflow")
        elif net_30 > Decimal("-50000"):
            cashflow_component = 45
            top_risk_factors.append("negative_cashflow")
        else:
            cashflow_component = 65
            top_risk_factors.append("critical_liquidity_pressure")

        company_campaigns = [c for c in marketing if c["company_id"] == company_id]
        low_roas_count = sum(1 for c in company_campaigns if c.get("roas") is not None and Decimal(str(c["roas"])) < Decimal("1.5"))
        if low_roas_count >= 10:
            marketing_component = 25
            top_risk_factors.append("multiple_low_roas_campaigns")
        elif low_roas_count >= 5:
            marketing_component = 15
            top_risk_factors.append("declining_marketing_efficiency")
        else:
            marketing_component = 5

        company_macros = [m for m in macros if m["company_id"] == company_id and m["metric_name"] == "USDTRY"]
        if company_macros:
            latest_fx = sorted(company_macros, key=lambda x: x["captured_at"])[-1]
            fx_val = Decimal(str(latest_fx["metric_value"]))
            if fx_val >= Decimal("35"):
                macro_component = 20
                top_risk_factors.append("fx_pressure")
            elif fx_val >= Decimal("33"):
                macro_component = 10

        total_score = min(100, cashflow_component + marketing_component + inventory_component + tax_component + macro_component)

        if total_score < 25:
            level = "low"
        elif total_score < 50:
            level = "medium"
        elif total_score < 75:
            level = "high"
        else:
            level = "critical"

        to_insert.append({
            "id": gen_uuid(),
            "company_id": company_id,
            "score_date": now_iso(),
            "overall_risk_score": total_score,
            "risk_level": level,
            "cashflow_component": cashflow_component,
            "marketing_component": marketing_component,
            "inventory_component": inventory_component,
            "tax_component": tax_component,
            "macro_component": macro_component,
            "top_risk_factors": top_risk_factors,
            "summary": f"Overall risk is {level} with score {total_score}",
            "created_at": now_iso(),
        })

    insert_rows(ai_cfo_db, "risk_scores", to_insert)


def main():
    """Main main for the service workflow."""
    print("Normalization + analytics başladı...")

    normalize_marketing_events()
    normalize_expense_invoice_events()
    normalize_bank_events()
    normalize_macro_events()
    generate_transaction_links()

    compute_cashflow_snapshots()
    compute_risk_scores()

    print("Normalization + analytics tamamlandı.")


if __name__ == "__main__":
    main()