from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


def _get_bool(name: str, default: bool = False) -> bool:
    """Read a boolean setting from environment variables."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_debug: bool = _get_bool("APP_DEBUG", True)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    agent_service_host: str = os.getenv("AGENT_SERVICE_HOST", "0.0.0.0")
    agent_service_port: int = int(os.getenv("AGENT_SERVICE_PORT", "8001"))

    ai_cfo_supabase_url: str | None = os.getenv("AI_CFO_SUPABASE_URL")
    ai_cfo_supabase_service_role_key: str | None = os.getenv("AI_CFO_SUPABASE_SERVICE_ROLE_KEY")

    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")

    def validate(self) -> None:
        """Validate validate before it is used by the service."""
        missing: list[str] = []

        if not self.ai_cfo_supabase_url:
            missing.append("AI_CFO_SUPABASE_URL")
        if not self.ai_cfo_supabase_service_role_key:
            missing.append("AI_CFO_SUPABASE_SERVICE_ROLE_KEY")
        if not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


settings = Settings()