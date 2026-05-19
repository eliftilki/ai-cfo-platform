from __future__ import annotations

from app.connectors.source_db import source_db


def get_first_company() -> dict | None:
    """Return first company."""
    response = source_db.table("companies").select("*").limit(1).execute()
    data = response.data or []
    return data[0] if data else None


def get_company_by_id(company_id: str) -> dict | None:
    """Return company by id."""
    response = source_db.table("companies").select("*").eq("id", company_id).limit(1).execute()
    data = response.data or []
    return data[0] if data else None