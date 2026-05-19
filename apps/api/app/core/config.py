from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file() -> None:
    """Load local environment variables from the service .env file."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _get_bool(name: str, default: bool = False) -> bool:
    """Read a boolean setting from environment variables."""
    value = os.getenv(name)
    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "on"}


_load_env_file()


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_debug: bool = _get_bool("APP_DEBUG", True)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    api_service_host: str = os.getenv("API_SERVICE_HOST", "0.0.0.0")
    api_service_port: int = int(os.getenv("API_SERVICE_PORT", "8000"))

    source_supabase_url: str = os.getenv("SOURCE_SUPABASE_URL", "")
    source_supabase_service_role_key: str = os.getenv(
        "SOURCE_SUPABASE_SERVICE_ROLE_KEY",
        "",
    )

    ai_cfo_supabase_url: str = os.getenv("AI_CFO_SUPABASE_URL", "")
    ai_cfo_supabase_service_role_key: str = os.getenv(
        "AI_CFO_SUPABASE_SERVICE_ROLE_KEY",
        "",
    )

    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    simulation_agent_model: str = os.getenv("SIMULATION_AGENT_MODEL", "gemini-2.5-flash")

    agent_service_base_url: str = os.getenv(
        "AGENT_SERVICE_BASE_URL",
        "http://localhost:8001",
    )

    # =========================================================
    # AUTH SETTINGS
    # =========================================================
    supabase_jwt_secret: str = os.getenv("SUPABASE_JWT_SECRET", "")
    supabase_auth_base_url: str = os.getenv(
        "SUPABASE_AUTH_BASE_URL",
        "",
    )

    def validate(self) -> None:
        """Validate validate before it is used by the service."""
        required = {
            "SOURCE_SUPABASE_URL": self.source_supabase_url,
            "SOURCE_SUPABASE_SERVICE_ROLE_KEY": self.source_supabase_service_role_key,
            "AI_CFO_SUPABASE_URL": self.ai_cfo_supabase_url,
            "AI_CFO_SUPABASE_SERVICE_ROLE_KEY": self.ai_cfo_supabase_service_role_key,
            "AGENT_SERVICE_BASE_URL": self.agent_service_base_url,
        }

        missing = [name for name, value in required.items() if not value]
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing required environment variables: {joined}")

    @property
    def resolved_supabase_auth_base_url(self) -> str:
        """Return the configured Supabase Auth base URL."""
        if self.supabase_auth_base_url:
            return self.supabase_auth_base_url.rstrip("/")
        return f"{self.ai_cfo_supabase_url.rstrip('/')}/auth/v1"


settings = Settings()
