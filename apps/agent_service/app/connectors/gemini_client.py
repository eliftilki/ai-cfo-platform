from __future__ import annotations

import google.generativeai as genai

from app.core.config import settings


settings.validate()

genai.configure(api_key=settings.gemini_api_key)


def get_gemini_model(model_name: str = "gemini-2.5-flash"):
    """Return gemini model."""
    return genai.GenerativeModel(model_name)