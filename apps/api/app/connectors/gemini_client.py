from __future__ import annotations

import google.generativeai as genai

from app.core.config import settings


_configured = False


def get_gemini_model(model_name: str | None = None):
    """Return gemini model."""
    global _configured

    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    if not _configured:
        genai.configure(api_key=settings.gemini_api_key)
        _configured = True

    return genai.GenerativeModel(model_name or settings.simulation_agent_model)