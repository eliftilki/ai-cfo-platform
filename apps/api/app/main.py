from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings


settings.validate()

app = FastAPI(
    title="AI CFO API Service",
    version="1.0.0",
)

app.include_router(api_router)
