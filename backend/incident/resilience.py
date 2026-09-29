"""
backend/incident/resilience.py
-------------------------------
F13 — Resilience Layer.

Provides health probing, exception wrapping, graceful degradation helpers,
and resilience status reporting across the Incident Response System.
"""

from __future__ import annotations

import logging
from backend.memory.hindsight import HindsightMemory, HindsightMemoryError

logger = logging.getLogger(__name__)

NO_MEMORY_WARNING = (
    "Memory temporarily unavailable — diagnosis is running without "
    "historical context."
)


async def is_hindsight_available(memory: HindsightMemory, probe_bank: str = "health-probe") -> bool:
    """
    Quick health-check: attempt to ensure a probe bank exists.
    Returns True if Hindsight responds, False otherwise.
    """
    try:
        await memory.ensure_bank(probe_bank)
        return True
    except (HindsightMemoryError, Exception) as exc:
        logger.warning("Hindsight health probe failed: %s", exc)
        return False


async def get_resilience_status(memory: HindsightMemory) -> dict:
    """
    Return comprehensive resilience and connectivity status of Hindsight.
    """
    available = await is_hindsight_available(memory)
    return {
        "hindsight_connected": available,
        "status": "online" if available else "degraded",
        "warning": None if available else NO_MEMORY_WARNING,
        "fallback_active": not available,
    }
