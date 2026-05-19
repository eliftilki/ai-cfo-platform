from __future__ import annotations

import os
import random
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from supabase import create_client


# =========================================================
# ENV
# =========================================================

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

SOURCE_SUPABASE_URL = os.getenv("SOURCE_SUPABASE_URL")
SOURCE_SUPABASE_SERVICE_ROLE_KEY = os.getenv("SOURCE_SUPABASE_SERVICE_ROLE_KEY")

AI_CFO_SUPABASE_URL = os.getenv("AI_CFO_SUPABASE_URL")
AI_CFO_SUPABASE_SERVICE_ROLE_KEY = os.getenv("AI_CFO_SUPABASE_SERVICE_ROLE_KEY")

if not SOURCE_SUPABASE_URL or not SOURCE_SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SOURCE_SUPABASE_URL or SOURCE_SUPABASE_SERVICE_ROLE_KEY")

if not AI_CFO_SUPABASE_URL or not AI_CFO_SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing AI_CFO_SUPABASE_URL or AI_CFO_SUPABASE_SERVICE_ROLE_KEY")

source_db = create_client(SOURCE_SUPABASE_URL, SOURCE_SUPABASE_SERVICE_ROLE_KEY)
ai_cfo_db = create_client(AI_CFO_SUPABASE_URL, AI_CFO_SUPABASE_SERVICE_ROLE_KEY)


# =========================================================
# CONFIG
# =========================================================

UTC = timezone.utc

COMPANY_ID = "5f4b5f3a-2d8f-4d34-9b2f-8e6e7f4d9001"
COMPANY_NAME = "GreenCart"
LEGAL_NAME = "GreenCart E-Ticaret A.Ş."

DAYS = 90
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# =========================================================
# HELPERS
# =========================================================

def now_utc() -> datetime:
    return datetime.now(UTC)


def iso(dt: datetime) -> str:
    return dt.isoformat()


def money(value: float | Decimal) -> float:
    return float(round(float(value), 2))


def new_id() -> str:
    return str(uuid.uuid4())


def insert_batches(client, table: str, rows: list[dict], batch_size: int = 500) -> None:
    if not rows:
        print(f"No rows for {table}")
        return

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        client.table(table).insert(batch).execute()
        print(f"Inserted {len(batch)} rows into {table}")


def safe_delete_company_rows(client, table: str, company_id: str) -> None:
    try:
        client.table(table).delete().eq("company_id", company_id).execute()
        print(f"Deleted old rows from {table}")
    except Exception as exc:
        print(f"Skipped delete for {table}: {exc}")


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# =========================================================
# CLEANUP
# =========================================================

def delete_source_company_data(company_id: str) -> None:
    tables = [
        "raw_macro_events",
        "raw_marketing_events",
        "raw_expense_invoice_events",
        "raw_bank_events",
        "sales_invoices",
        "payments",
        "order_items",
        "orders",
        "purchase_orders",
        "inventory",
        "products",
        "suppliers",
        "customers",
        "companies",
    ]

    for table in tables:
        safe_delete_company_rows(source_db, table, company_id)


def delete_ai_cfo_company_data(company_id: str) -> None:
    tables = [
        "transaction_links",
        "simulations",
        "decisions",
        "dashboard_snapshot_history",
        "dashboard_snapshot_latest",
        "dashboard_snapshots",
        "dashboard_refresh_state",
        "alerts",
        "risk_scores",
        "macro_market_data",
        "expense_invoices",
        "marketing_campaigns",
        "cashflow_snapshots",
        "agent_outputs",
        "agent_runs",
        "bank_transactions",
        "companies",
    ]

    for table in tables:
        safe_delete_company_rows(ai_cfo_db, table, company_id)


# =========================================================
# SOURCE DB: COMPANY
# =========================================================

def source_company_row() -> dict:
    return {
        "id": COMPANY_ID,
        "name": COMPANY_NAME,
        "legal_name": LEGAL_NAME,
        "tax_number": "1234567890",
        "industry": "ecommerce",
        "country_code": "TR",
        "currency_code": "TRY",
        "timezone": "Europe/Istanbul",
        "website_url": "https://greencart.example.com",
        "status": "active",
        "created_at": iso(now_utc() - timedelta(days=180)),
        "updated_at": iso(now_utc()),
    }


def ai_cfo_company_row() -> dict:
    return {
        "id": COMPANY_ID,
        "name": COMPANY_NAME,
        "created_at": iso(now_utc() - timedelta(days=180)),
        "updated_at": iso(now_utc()),
    }


# =========================================================
# SOURCE DB: CUSTOMERS
# =========================================================

def generate_customers(count: int = 900) -> list[dict]:
    cities = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Kocaeli", "Eskişehir"]
    acquisition_channels = ["organic", "instagram", "google_ads", "marketplace", "referral", "direct"]

    rows: list[dict] = []

    for i in range(count):
        created_at = now_utc() - timedelta(days=random.randint(30, 180))

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "external_customer_code": f"GC-CUST-{i + 1:05d}",
                "full_name": f"GreenCart Customer {i + 1}",
                "email": f"customer{i + 1}@example.com",
                "phone": f"+90555{random.randint(1000000, 9999999)}",
                "city": random.choice(cities),
                "state_region": None,
                "country_code": "TR",
                "segment": random.choices(
                    ["new", "returning", "loyal", "at_risk"],
                    weights=[25, 45, 25, 5],
                    k=1,
                )[0],
                "acquisition_channel": random.choices(
                    acquisition_channels,
                    weights=[30, 18, 25, 15, 7, 5],
                    k=1,
                )[0],
                "first_order_at": None,
                "last_order_at": None,
                "is_active": True,
                "created_at": iso(created_at),
                "updated_at": iso(now_utc()),
            }
        )

    return rows


# =========================================================
# SOURCE DB: SUPPLIERS
# =========================================================

def generate_suppliers(count: int = 12) -> list[dict]:
    categories = [
        "organic_food",
        "fresh_produce",
        "eco_cleaning",
        "packaging",
        "logistics",
    ]

    cities = ["İstanbul", "Ankara", "İzmir", "Bursa"]

    rows: list[dict] = []

    for i in range(count):
        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "supplier_code": f"GC-SUP-{i + 1:04d}",
                "supplier_name": f"Green Supplier {i + 1}",
                "contact_name": f"Supplier Contact {i + 1}",
                "email": f"supplier{i + 1}@example.com",
                "phone": f"+90212{random.randint(1000000, 9999999)}",
                "city": random.choice(cities),
                "state_region": None,
                "country_code": "TR",
                "category": random.choice(categories),
                "payment_terms_days": random.choice([30, 45, 60]),
                "is_active": True,
                "created_at": iso(now_utc() - timedelta(days=random.randint(90, 240))),
                "updated_at": iso(now_utc()),
            }
        )

    return rows


# =========================================================
# SOURCE DB: PRODUCTS + INVENTORY
# =========================================================

def generate_products(suppliers: list[dict], count: int = 60) -> list[dict]:
    categories = [
        ("Organic Food", "Pantry"),
        ("Healthy Snacks", "Snacks"),
        ("Fresh Box", "Fresh"),
        ("Eco Cleaning", "Cleaning"),
        ("Subscription Box", "Subscription"),
    ]

    rows: list[dict] = []

    for i in range(count):
        category, subcategory = random.choice(categories)
        supplier = random.choice(suppliers)

        if category == "Organic Food":
            cost = random.uniform(60, 130)
            price = cost * random.uniform(1.75, 2.45)
        elif category == "Healthy Snacks":
            cost = random.uniform(25, 70)
            price = cost * random.uniform(1.9, 2.7)
        elif category == "Fresh Box":
            cost = random.uniform(120, 250)
            price = cost * random.uniform(1.55, 2.1)
        elif category == "Eco Cleaning":
            cost = random.uniform(45, 110)
            price = cost * random.uniform(1.8, 2.5)
        else:
            cost = random.uniform(180, 360)
            price = cost * random.uniform(1.6, 2.3)

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "supplier_id": supplier["id"],
                "sku": f"GC-{i + 1:04d}",
                "barcode": f"869{random.randint(1000000000, 9999999999)}",
                "product_name": f"{category} Product {i + 1}",
                "category": category,
                "subcategory": subcategory,
                "brand": "GreenCart",
                "description": f"{category} demo product",
                "cost_price": money(cost),
                "list_price": money(price),
                "vat_rate": 20.0,
                "weight_grams": money(random.uniform(100, 2500)),
                "is_active": True,
                "launched_at": iso(now_utc() - timedelta(days=random.randint(90, 240))),
                "created_at": iso(now_utc() - timedelta(days=random.randint(90, 240))),
                "updated_at": iso(now_utc()),
            }
        )

    return rows


def generate_inventory(products: list[dict]) -> list[dict]:
    rows: list[dict] = []

    for product in products:
        stock_level = random.randint(120, 900)
        reserved_stock = random.randint(0, 40)
        reorder_level = random.randint(30, 90)
        safety_stock = random.randint(20, 60)
        stock_value = Decimal(str(product["cost_price"])) * Decimal(stock_level)

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "product_id": product["id"],
                "stock_level": stock_level,
                "reserved_stock": reserved_stock,
                "reorder_level": reorder_level,
                "safety_stock": safety_stock,
                "warehouse_location": random.choice(["IST-WH-1", "IST-WH-2", "ANK-WH-1"]),
                "stock_value": money(stock_value),
                "last_restocked_at": iso(now_utc() - timedelta(days=random.randint(1, 30))),
                "updated_at": iso(now_utc()),
            }
        )

    return rows


# =========================================================
# SOURCE DB: ORDERS, ITEMS, PAYMENTS, SALES INVOICES
# =========================================================

def generate_orders_bundle(
    customers: list[dict],
    products: list[dict],
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    orders: list[dict] = []
    order_items: list[dict] = []
    payments: list[dict] = []
    invoices: list[dict] = []

    customer_first_last: dict[str, dict[str, str]] = {}

    base_date = now_utc() - timedelta(days=DAYS)
    order_number = 1

    for day in range(DAYS):
        current_date = base_date + timedelta(days=day)

        if current_date.weekday() >= 5:
            daily_order_count = random.randint(22, 40)
        else:
            daily_order_count = random.randint(38, 68)

        for _ in range(daily_order_count):
            order_id = new_id()
            customer = random.choice(customers)

            order_date = current_date + timedelta(
                hours=random.randint(8, 22),
                minutes=random.randint(0, 59),
            )

            selected_products = random.sample(products, k=random.randint(1, 4))

            subtotal = Decimal("0")
            total_tax = Decimal("0")

            for product in selected_products:
                quantity = random.randint(1, 3)
                unit_price = Decimal(str(product["list_price"]))
                discount_rate = Decimal(str(random.choice([0, 0, 0, 3, 5, 8])))
                gross_line = unit_price * Decimal(quantity)
                discount_amount = gross_line * discount_rate / Decimal("100")
                net_line = gross_line - discount_amount
                tax_rate = Decimal(str(product["vat_rate"]))
                tax_amount = net_line * tax_rate / Decimal("100")
                line_total = net_line + tax_amount

                subtotal += net_line
                total_tax += tax_amount

                order_items.append(
                    {
                        "id": new_id(),
                        "company_id": COMPANY_ID,
                        "order_id": order_id,
                        "product_id": product["id"],
                        "quantity": quantity,
                        "unit_price": money(unit_price),
                        "discount_rate": money(discount_rate),
                        "discount_amount": money(discount_amount),
                        "tax_rate": money(tax_rate),
                        "line_total": money(line_total),
                        "created_at": iso(order_date),
                    }
                )

            shipping_fee = Decimal(str(random.choice([0, 39.9, 49.9, 59.9])))
            total_amount = subtotal + total_tax + shipping_fee

            status = random.choices(
                ["delivered", "shipped", "processing", "cancelled", "returned"],
                weights=[78, 8, 6, 4, 4],
                k=1,
            )[0]

            sales_channel = random.choices(
                ["website", "marketplace", "instagram", "google_ads", "direct"],
                weights=[42, 20, 15, 18, 5],
                k=1,
            )[0]

            orders.append(
                {
                    "id": order_id,
                    "company_id": COMPANY_ID,
                    "customer_id": customer["id"],
                    "order_number": f"GC-ORD-{order_number:06d}",
                    "order_date": iso(order_date),
                    "status": status,
                    "sales_channel": sales_channel,
                    "currency_code": "TRY",
                    "subtotal_amount": money(subtotal),
                    "discount_amount": 0,
                    "shipping_fee": money(shipping_fee),
                    "tax_amount": money(total_tax),
                    "total_amount": money(total_amount),
                    "notes": None,
                    "created_at": iso(order_date),
                    "updated_at": iso(order_date),
                }
            )

            if customer["id"] not in customer_first_last:
                customer_first_last[customer["id"]] = {
                    "first_order_at": iso(order_date),
                    "last_order_at": iso(order_date),
                }
            else:
                customer_first_last[customer["id"]]["last_order_at"] = iso(order_date)

            if status not in {"cancelled"}:
                payment_status = random.choices(
                    ["paid", "pending", "refunded", "partially_refunded", "failed"],
                    weights=[90, 4, 3, 2, 1],
                    k=1,
                )[0]

                paid_amount = total_amount
                if payment_status == "refunded":
                    paid_amount = Decimal("0")
                elif payment_status == "partially_refunded":
                    paid_amount = total_amount * Decimal("0.7")
                elif payment_status == "failed":
                    paid_amount = Decimal("0")

                payment_date = order_date + timedelta(hours=random.randint(0, 36))

                payments.append(
                    {
                        "id": new_id(),
                        "company_id": COMPANY_ID,
                        "order_id": order_id,
                        "payment_date": iso(payment_date),
                        "payment_method": random.choice(
                            ["credit_card", "debit_card", "bank_transfer", "wallet"]
                        ),
                        "installment_count": random.choice([1, 1, 1, 2, 3]),
                        "paid_amount": money(paid_amount),
                        "payment_status": payment_status,
                        "settlement_provider": random.choice(
                            ["iyzico", "paytr", "stripe", "manual"]
                        ),
                        "provider_transaction_ref": f"PAY-{uuid.uuid4().hex[:16]}",
                        "created_at": iso(payment_date),
                        "updated_at": iso(payment_date),
                    }
                )

                invoice_status = "issued"
                if status == "returned" or payment_status in {"refunded", "partially_refunded"}:
                    invoice_status = "refunded"

                invoices.append(
                    {
                        "id": new_id(),
                        "company_id": COMPANY_ID,
                        "order_id": order_id,
                        "invoice_number": f"GC-INV-{order_number:06d}",
                        "invoice_date": iso(order_date),
                        "subtotal": money(subtotal),
                        "tax_amount": money(total_tax),
                        "total_amount": money(total_amount),
                        "invoice_status": invoice_status,
                        "created_at": iso(order_date),
                        "updated_at": iso(order_date),
                    }
                )

            order_number += 1

    # customers first/last order update is optional. It requires update calls.
    for customer in customers:
        info = customer_first_last.get(customer["id"])
        if info:
            customer["first_order_at"] = info["first_order_at"]
            customer["last_order_at"] = info["last_order_at"]
            customer["segment"] = random.choices(
                ["returning", "loyal", "new"],
                weights=[45, 40, 15],
                k=1,
            )[0]

    return orders, order_items, payments, invoices


# =========================================================
# SOURCE DB: PURCHASE ORDERS
# =========================================================

def generate_purchase_orders(suppliers: list[dict], products: list[dict]) -> list[dict]:
    rows: list[dict] = []
    base_date = now_utc() - timedelta(days=DAYS)

    for index in range(1, 45):
        supplier = random.choice(suppliers)
        order_date = base_date + timedelta(days=random.randint(0, DAYS - 1), hours=random.randint(9, 17))

        selected_products = [
            p for p in products if p["supplier_id"] == supplier["id"]
        ]

        if len(selected_products) < 3:
            selected_products = products

        selected_products = random.sample(selected_products, k=random.randint(3, min(8, len(selected_products))))

        subtotal = Decimal("0")
        for product in selected_products:
            quantity = random.randint(20, 100)
            subtotal += Decimal(str(product["cost_price"])) * Decimal(quantity)

        tax_amount = subtotal * Decimal("0.20")
        shipping_cost = Decimal(str(random.uniform(500, 3500)))
        total_cost = subtotal + tax_amount + shipping_cost

        expected_delivery = order_date + timedelta(days=random.randint(3, 10))
        actual_delivery = expected_delivery + timedelta(days=random.choice([-1, 0, 1, 2]))

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "supplier_id": supplier["id"],
                "po_number": f"GC-PO-{index:05d}",
                "order_date": iso(order_date),
                "expected_delivery_date": iso(expected_delivery),
                "actual_delivery_date": iso(actual_delivery),
                "status": random.choices(
                    ["received", "partially_received", "ordered"],
                    weights=[75, 15, 10],
                    k=1,
                )[0],
                "currency_code": "TRY",
                "subtotal_amount": money(subtotal),
                "tax_amount": money(tax_amount),
                "shipping_cost": money(shipping_cost),
                "total_cost": money(total_cost),
                "notes": None,
                "created_at": iso(order_date),
                "updated_at": iso(order_date),
            }
        )

    return rows


# =========================================================
# SOURCE DB: RAW EVENTS
# =========================================================

def generate_raw_bank_events(payments: list[dict], purchase_orders: list[dict]) -> list[dict]:
    rows: list[dict] = []

    for payment in payments:
        if payment["payment_status"] != "paid":
            continue

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "event_type": "bank_transaction_created",
                "source": "mock_bank_feed",
                "external_event_id": f"BANK-IN-{payment['id']}",
                "event_date": payment["payment_date"],
                "payload": {
                    "direction": "income",
                    "amount": payment["paid_amount"],
                    "currency_code": "TRY",
                    "description": "Sales payment settlement",
                    "source_entity_type": "payment",
                    "source_entity_ref": payment["id"],
                },
                "is_processed": False,
                "processed_at": None,
                "created_at": iso(now_utc()),
            }
        )

    for po in purchase_orders:
        if po["status"] not in {"received", "partially_received"}:
            continue

        payment_date = parse_dt(po["order_date"]) + timedelta(days=random.randint(10, 35))

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "event_type": "bank_transaction_created",
                "source": "mock_bank_feed",
                "external_event_id": f"BANK-OUT-{po['id']}",
                "event_date": iso(payment_date),
                "payload": {
                    "direction": "expense",
                    "amount": po["total_cost"],
                    "currency_code": "TRY",
                    "description": "Supplier payment",
                    "source_entity_type": "purchase_order",
                    "source_entity_ref": po["id"],
                },
                "is_processed": False,
                "processed_at": None,
                "created_at": iso(now_utc()),
            }
        )

    return rows


def generate_raw_marketing_events() -> list[dict]:
    rows: list[dict] = []
    base_date = now_utc() - timedelta(days=DAYS)

    platforms = ["Meta", "Google Ads"]
    categories = ["Organic Food", "Healthy Snacks", "Fresh Box", "Eco Cleaning", "Subscription Box"]

    idx = 1
    for week in range(13):
        for platform in platforms:
            start = base_date + timedelta(days=week * 7 + random.randint(0, 2))
            end = start + timedelta(days=random.randint(5, 10))

            spend = random.uniform(18000, 65000)
            roas = random.uniform(2.5, 3.7) if platform == "Google Ads" else random.uniform(2.1, 3.2)
            revenue = spend * roas
            clicks = random.randint(2500, 9500)
            impressions = clicks * random.randint(25, 55)
            conversions = random.randint(180, 620)
            orders = int(conversions * random.uniform(0.72, 0.9))
            category = random.choice(categories)

            rows.append(
                {
                    "id": new_id(),
                    "company_id": COMPANY_ID,
                    "event_type": "campaign_performance_reported",
                    "source": "mock_marketing_feed",
                    "external_event_id": f"MKT-EVT-{idx:05d}",
                    "event_date": iso(end),
                    "payload": {
                        "external_campaign_id": f"MKT-CAMP-{idx:05d}",
                        "campaign_name": f"{platform}_{category.replace(' ', '_')}_W{week + 1:02d}",
                        "platform": platform,
                        "target_category": category,
                        "campaign_start_at": iso(start),
                        "campaign_end_at": iso(end),
                        "ad_spend": money(spend),
                        "impressions": impressions,
                        "clicks": clicks,
                        "conversions": conversions,
                        "attributed_orders": orders,
                        "attributed_revenue": money(revenue),
                        "roas": float(round(roas, 2)),
                        "cac": money(spend / conversions),
                        "status": "completed" if end < now_utc() else "active",
                    },
                    "is_processed": False,
                    "processed_at": None,
                    "created_at": iso(now_utc()),
                }
            )
            idx += 1

    return rows


def generate_raw_expense_invoice_events(purchase_orders: list[dict]) -> list[dict]:
    rows: list[dict] = []

    for i, po in enumerate(purchase_orders, start=1):
        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "event_type": "expense_invoice_received",
                "source": "mock_invoice_feed",
                "external_event_id": f"EXP-EVT-{i:05d}",
                "event_date": po["order_date"],
                "payload": {
                    "external_invoice_id": f"EXP-INV-{i:05d}",
                    "invoice_number": f"GC-EXP-{i:05d}",
                    "invoice_type": "purchase",
                    "vendor_name": f"Supplier PO {po['po_number']}",
                    "vendor_category": "supplier_payment",
                    "invoice_date": po["order_date"],
                    "due_date": iso(parse_dt(po["order_date"]) + timedelta(days=30)),
                    "subtotal": po["subtotal_amount"],
                    "tax_amount": po["tax_amount"],
                    "total_amount": po["total_cost"],
                    "currency_code": "TRY",
                    "payment_status": "paid" if po["status"] == "received" else "open",
                    "related_purchase_order_number": po["po_number"],
                },
                "is_processed": False,
                "processed_at": None,
                "created_at": iso(now_utc()),
            }
        )

    return rows


def generate_raw_macro_events() -> list[dict]:
    rows: list[dict] = []
    base_date = now_utc() - timedelta(days=DAYS)

    for day in range(0, DAYS, 7):
        event_date = base_date + timedelta(days=day)

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "event_type": "macro_metric_reported",
                "source": "mock_macro_feed",
                "external_event_id": f"MACRO-USDTRY-{day:03d}",
                "event_date": iso(event_date),
                "payload": {
                    "external_metric_id": f"USDTRY-{day:03d}",
                    "metric_name": "USDTRY",
                    "metric_value": round(32.0 + day * 0.015 + random.uniform(-0.15, 0.15), 4),
                    "metric_unit": "TRY",
                    "captured_at": iso(event_date),
                    "source": "mock_macro_feed",
                },
                "is_processed": False,
                "processed_at": None,
                "created_at": iso(now_utc()),
            }
        )

    return rows


# =========================================================
# AI CFO NORMALIZED DATA
# =========================================================

def generate_ai_cfo_bank_transactions(
    payments: list[dict],
    purchase_orders: list[dict],
) -> list[dict]:
    rows: list[dict] = []

    for payment in payments:
        if payment["payment_status"] != "paid":
            continue

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "external_transaction_id": f"BT-IN-{payment['id']}",
                "transaction_date": payment["payment_date"],
                "amount": payment["paid_amount"],
                "currency_code": "TRY",
                "direction": "income",
                "description": "Satış tahsilatı",
                "merchant_name": "GreenCart Customer",
                "category": "satis tahsilatlari",
                "source_entity_type": "payment",
                "source_entity_ref": payment["id"],
                "gross_paid": payment["paid_amount"],
                "commission_rate": 0.025,
                "raw_event_id": f"BANK-IN-{payment['id']}",
                "created_at": iso(now_utc()),
                "updated_at": iso(now_utc()),
            }
        )

    for po in purchase_orders:
        if po["status"] not in {"received", "partially_received"}:
            continue

        transaction_date = parse_dt(po["order_date"]) + timedelta(days=random.randint(10, 35))

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "external_transaction_id": f"BT-OUT-{po['id']}",
                "transaction_date": iso(transaction_date),
                "amount": po["total_cost"],
                "currency_code": "TRY",
                "direction": "expense",
                "description": "Tedarikçi ödemesi",
                "merchant_name": "Green Supplier",
                "category": "tedarikci odemeleri",
                "source_entity_type": "purchase_order",
                "source_entity_ref": po["id"],
                "gross_paid": po["total_cost"],
                "commission_rate": None,
                "raw_event_id": f"BANK-OUT-{po['id']}",
                "created_at": iso(now_utc()),
                "updated_at": iso(now_utc()),
            }
        )

    # Sağlıklı şirket için kontrollü operasyonel giderler
    base_date = now_utc() - timedelta(days=DAYS)

    for day in range(DAYS):
        current_date = base_date + timedelta(days=day)

        if day % 3 == 0:
            amount = random.uniform(4000, 13000)
            rows.append(
                {
                    "id": new_id(),
                    "company_id": COMPANY_ID,
                    "external_transaction_id": f"BT-OPS-{day:03d}",
                    "transaction_date": iso(current_date + timedelta(hours=14)),
                    "amount": money(amount),
                    "currency_code": "TRY",
                    "direction": "expense",
                    "description": "Operasyonel gider",
                    "merchant_name": "Operations Vendor",
                    "category": random.choice(["kargo giderleri", "depo giderleri", "personel giderleri", "yazilim giderleri"]),
                    "source_entity_type": "manual_expense",
                    "source_entity_ref": f"OPS-{day:03d}",
                    "gross_paid": money(amount),
                    "commission_rate": None,
                    "raw_event_id": f"OPS-{day:03d}",
                    "created_at": iso(now_utc()),
                    "updated_at": iso(now_utc()),
                }
            )

    return rows


def generate_ai_cfo_marketing_campaigns(raw_marketing_events: list[dict]) -> list[dict]:
    rows: list[dict] = []

    for event in raw_marketing_events:
        p = event["payload"]

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "external_campaign_id": p["external_campaign_id"],
                "campaign_name": p["campaign_name"],
                "platform": p["platform"],
                "target_category": p["target_category"],
                "campaign_start_at": p["campaign_start_at"],
                "campaign_end_at": p["campaign_end_at"],
                "ad_spend": p["ad_spend"],
                "impressions": p["impressions"],
                "clicks": p["clicks"],
                "conversions": p["conversions"],
                "attributed_orders": p["attributed_orders"],
                "attributed_revenue": p["attributed_revenue"],
                "roas": p["roas"],
                "cac": p["cac"],
                "status": p["status"],
                "raw_event_id": event["external_event_id"],
                "created_at": iso(now_utc()),
                "updated_at": iso(now_utc()),
            }
        )

    return rows


def generate_ai_cfo_expense_invoices(raw_expense_events: list[dict]) -> list[dict]:
    rows: list[dict] = []

    for event in raw_expense_events:
        p = event["payload"]

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "external_invoice_id": p["external_invoice_id"],
                "invoice_number": p["invoice_number"],
                "invoice_type": p["invoice_type"],
                "vendor_name": p["vendor_name"],
                "vendor_category": p["vendor_category"],
                "invoice_date": p["invoice_date"],
                "due_date": p["due_date"],
                "subtotal": p["subtotal"],
                "tax_amount": p["tax_amount"],
                "total_amount": p["total_amount"],
                "currency_code": p["currency_code"],
                "payment_status": p["payment_status"],
                "related_purchase_order_number": p["related_purchase_order_number"],
                "related_campaign_id": None,
                "related_campaign_name": None,
                "raw_event_id": event["external_event_id"],
                "created_at": iso(now_utc()),
                "updated_at": iso(now_utc()),
            }
        )

    return rows


def generate_ai_cfo_macro_market_data(raw_macro_events: list[dict]) -> list[dict]:
    rows: list[dict] = []

    for event in raw_macro_events:
        p = event["payload"]

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "external_metric_id": p["external_metric_id"],
                "metric_name": p["metric_name"],
                "metric_value": p["metric_value"],
                "metric_unit": p["metric_unit"],
                "captured_at": p["captured_at"],
                "source": p["source"],
                "raw_event_id": event["external_event_id"],
                "created_at": iso(now_utc()),
                "updated_at": iso(now_utc()),
            }
        )

    return rows


# =========================================================
# AI CFO SNAPSHOTS / RISK / ALERTS
# =========================================================

def summarize_cashflow(transactions: list[dict], end_date: datetime, days: int) -> dict:
    start_date = end_date - timedelta(days=days)

    income = Decimal("0")
    expense = Decimal("0")

    for tx in transactions:
        tx_date = parse_dt(tx["transaction_date"])
        if not (start_date <= tx_date <= end_date):
            continue

        amount = Decimal(str(tx["amount"]))

        if tx["direction"] == "income":
            income += amount
        elif tx["direction"] == "expense":
            expense += amount

    net = income - expense

    if net < 0:
        risk = "medium"
    elif expense > 0 and income / expense < Decimal("1.15"):
        risk = "medium"
    else:
        risk = "low"

    return {
        "income": money(income),
        "expense": money(expense),
        "net": money(net),
        "risk": risk,
    }


def summarize_marketing(campaigns: list[dict], end_date: datetime, days: int) -> dict:
    start_date = end_date - timedelta(days=days)

    spend = Decimal("0")
    revenue = Decimal("0")

    for c in campaigns:
        start = parse_dt(c["campaign_start_at"])
        if not (start_date <= start <= end_date):
            continue

        spend += Decimal(str(c["ad_spend"]))
        revenue += Decimal(str(c["attributed_revenue"]))

    roas = revenue / spend if spend > 0 else Decimal("0")

    if roas >= Decimal("2.5"):
        risk = "low"
    elif roas >= Decimal("1.8"):
        risk = "medium"
    else:
        risk = "high"

    return {
        "spend": money(spend),
        "revenue": money(revenue),
        "roas": float(round(roas, 2)),
        "risk": risk,
    }


def generate_cashflow_snapshots(bank_transactions: list[dict]) -> list[dict]:
    rows: list[dict] = []

    for offset in range(84, -1, -7):
        snapshot_date = now_utc() - timedelta(days=offset)

        s7 = summarize_cashflow(bank_transactions, snapshot_date, 7)
        s30 = summarize_cashflow(bank_transactions, snapshot_date, 30)

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "snapshot_date": iso(snapshot_date),
                "income_7d": s7["income"],
                "expense_7d": s7["expense"],
                "net_cashflow_7d": s7["net"],
                "income_30d": s30["income"],
                "expense_30d": s30["expense"],
                "net_cashflow_30d": s30["net"],
                "liquidity_risk": s30["risk"],
                "summary": f"30d net cashflow: {s30['net']}, liquidity risk: {s30['risk']}",
                "created_at": iso(snapshot_date),
            }
        )

    return rows


def generate_risk_scores(bank_transactions: list[dict], campaigns: list[dict]) -> list[dict]:
    rows: list[dict] = []

    for offset in range(84, -1, -14):
        score_date = now_utc() - timedelta(days=offset)

        cf = summarize_cashflow(bank_transactions, score_date, 30)
        mk = summarize_marketing(campaigns, score_date, 60)

        cashflow_component = 15 if cf["risk"] == "low" else 35
        marketing_component = 15 if mk["risk"] == "low" else 35

        overall = int(cashflow_component * 0.6 + marketing_component * 0.4)

        if overall < 25:
            level = "low"
        elif overall < 50:
            level = "medium"
        elif overall < 75:
            level = "high"
        else:
            level = "critical"

        factors = []
        if cf["net"] > 0:
            factors.append("positive_30d_cashflow")
        if mk["roas"] >= 2.5:
            factors.append("strong_marketing_efficiency")
        if not factors:
            factors.append("stable_operations")

        rows.append(
            {
                "id": new_id(),
                "company_id": COMPANY_ID,
                "score_date": iso(score_date),
                "overall_risk_score": overall,
                "risk_level": level,
                "cashflow_component": cashflow_component,
                "marketing_component": marketing_component,
                "inventory_component": 10,
                "tax_component": 10,
                "macro_component": 10,
                "top_risk_factors": factors,
                "summary": f"Risk score {overall}, level {level}. Cashflow net {cf['net']}, marketing ROAS {mk['roas']}.",
                "created_at": iso(score_date),
            }
        )

    return rows


def generate_alerts() -> list[dict]:
    return [
        {
            "id": new_id(),
            "company_id": COMPANY_ID,
            "alert_type": "cashflow_health",
            "severity": "info",
            "title": "Pozitif nakit akışı",
            "message": "Son dönem nakit akışı pozitif seyrediyor. Mevcut ödeme disiplini korunmalı.",
            "related_entity_type": "cashflow",
            "related_entity_id": None,
            "is_read": False,
            "created_at": iso(now_utc() - timedelta(days=2)),
        },
        {
            "id": new_id(),
            "company_id": COMPANY_ID,
            "alert_type": "marketing_efficiency",
            "severity": "info",
            "title": "Reklam verimliliği güçlü",
            "message": "Genel ROAS sağlıklı seviyede. Bütçe artışları kontrollü testlerle değerlendirilebilir.",
            "related_entity_type": "marketing",
            "related_entity_id": None,
            "is_read": False,
            "created_at": iso(now_utc() - timedelta(days=1)),
        },
    ]


def generate_dashboard_refresh_state() -> dict:
    return {
        "company_id": COMPANY_ID,
        "cashflow_dirty": True,
        "marketing_dirty": True,
        "risk_dirty": True,
        "alerts_dirty": True,
        "cashflow_last_refreshed_at": None,
        "marketing_last_refreshed_at": None,
        "risk_last_refreshed_at": None,
        "alerts_last_refreshed_at": None,
        "pending_cashflow_events": 0,
        "pending_marketing_events": 0,
        "pending_alert_events": 0,
        "pending_risk_events": 0,
        "daily_snapshot_last_created_at": None,
        "updated_at": iso(now_utc()),
        "created_at": iso(now_utc()),
    }


# =========================================================
# MAIN
# =========================================================

def main() -> None:
    print("Deleting old company data...")
    delete_ai_cfo_company_data(COMPANY_ID)
    delete_source_company_data(COMPANY_ID)

    print("\nGenerating source/kobiDB data...")
    company = source_company_row()
    customers = generate_customers(900)
    suppliers = generate_suppliers(12)
    products = generate_products(suppliers, 60)
    inventory = generate_inventory(products)
    orders, order_items, payments, sales_invoices = generate_orders_bundle(customers, products)
    purchase_orders = generate_purchase_orders(suppliers, products)

    raw_bank_events = generate_raw_bank_events(payments, purchase_orders)
    raw_marketing_events = generate_raw_marketing_events()
    raw_expense_invoice_events = generate_raw_expense_invoice_events(purchase_orders)
    raw_macro_events = generate_raw_macro_events()

    print("\nInserting source/kobiDB data...")
    source_db.table("companies").upsert(company, on_conflict="id").execute()
    insert_batches(source_db, "customers", customers)
    insert_batches(source_db, "suppliers", suppliers)
    insert_batches(source_db, "products", products)
    insert_batches(source_db, "inventory", inventory)
    insert_batches(source_db, "orders", orders)
    insert_batches(source_db, "order_items", order_items)
    insert_batches(source_db, "payments", payments)
    insert_batches(source_db, "sales_invoices", sales_invoices)
    insert_batches(source_db, "purchase_orders", purchase_orders)
    insert_batches(source_db, "raw_bank_events", raw_bank_events)
    insert_batches(source_db, "raw_marketing_events", raw_marketing_events)
    insert_batches(source_db, "raw_expense_invoice_events", raw_expense_invoice_events)
    insert_batches(source_db, "raw_macro_events", raw_macro_events)

    print("\nGenerating AI_CFO normalized data...")
    ai_company = ai_cfo_company_row()
    ai_bank_transactions = generate_ai_cfo_bank_transactions(payments, purchase_orders)
    ai_marketing_campaigns = generate_ai_cfo_marketing_campaigns(raw_marketing_events)
    ai_expense_invoices = generate_ai_cfo_expense_invoices(raw_expense_invoice_events)
    ai_macro_market_data = generate_ai_cfo_macro_market_data(raw_macro_events)
    ai_cashflow_snapshots = generate_cashflow_snapshots(ai_bank_transactions)
    ai_risk_scores = generate_risk_scores(ai_bank_transactions, ai_marketing_campaigns)
    ai_alerts = generate_alerts()
    dashboard_refresh_state = generate_dashboard_refresh_state()

    print("\nInserting AI_CFO normalized data...")
    ai_cfo_db.table("companies").upsert(ai_company, on_conflict="id").execute()
    insert_batches(ai_cfo_db, "bank_transactions", ai_bank_transactions)
    insert_batches(ai_cfo_db, "marketing_campaigns", ai_marketing_campaigns)
    insert_batches(ai_cfo_db, "expense_invoices", ai_expense_invoices)
    insert_batches(ai_cfo_db, "macro_market_data", ai_macro_market_data)
    insert_batches(ai_cfo_db, "cashflow_snapshots", ai_cashflow_snapshots)
    insert_batches(ai_cfo_db, "risk_scores", ai_risk_scores)
    insert_batches(ai_cfo_db, "alerts", ai_alerts)

    ai_cfo_db.table("dashboard_refresh_state").upsert(
        dashboard_refresh_state,
        on_conflict="company_id",
    ).execute()

    print("\nSeed completed.")
    print(f"Company ID: {COMPANY_ID}")
    print(f"Company Name: {COMPANY_NAME}")
    print("--- Source/kobiDB ---")
    print(f"Customers: {len(customers)}")
    print(f"Suppliers: {len(suppliers)}")
    print(f"Products: {len(products)}")
    print(f"Inventory: {len(inventory)}")
    print(f"Orders: {len(orders)}")
    print(f"Order items: {len(order_items)}")
    print(f"Payments: {len(payments)}")
    print(f"Sales invoices: {len(sales_invoices)}")
    print(f"Purchase orders: {len(purchase_orders)}")
    print(f"Raw bank events: {len(raw_bank_events)}")
    print(f"Raw marketing events: {len(raw_marketing_events)}")
    print(f"Raw expense invoice events: {len(raw_expense_invoice_events)}")
    print(f"Raw macro events: {len(raw_macro_events)}")
    print("--- AI_CFO ---")
    print(f"Bank transactions: {len(ai_bank_transactions)}")
    print(f"Marketing campaigns: {len(ai_marketing_campaigns)}")
    print(f"Expense invoices: {len(ai_expense_invoices)}")
    print(f"Macro market data: {len(ai_macro_market_data)}")
    print(f"Cashflow snapshots: {len(ai_cashflow_snapshots)}")
    print(f"Risk scores: {len(ai_risk_scores)}")
    print(f"Alerts: {len(ai_alerts)}")


if __name__ == "__main__":
    main()