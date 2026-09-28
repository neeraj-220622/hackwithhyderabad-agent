"""
backend/config.py
-----------------
Central configuration loaded from environment variables (and an optional .env file).
All other modules import from here — never from os.environ directly.
"""

import os
from dotenv import load_dotenv

# Load .env if it exists (silently skipped in production where env vars are injected)
load_dotenv()


class Config:
    # ── LLM ──────────────────────────────────────────────────────────────────
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")

    # ── Hindsight (future) ────────────────────────────────────────────────────
    HINDSIGHT_URL: str | None = os.getenv("HINDSIGHT_URL")
    HINDSIGHT_API_KEY: str | None = os.getenv("HINDSIGHT_API_KEY")


config = Config()
