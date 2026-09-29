"""
backend/incident/memory_inspector.py
--------------------------------------
F9 — Memory Inspector.

Allows engineers and evaluators to inspect real Hindsight incident memories.
"""

from __future__ import annotations

import logging
from backend.memory.hindsight import HindsightMemory, HindsightMemoryError

logger = logging.getLogger(__name__)


async def inspect_memories(
    memory: HindsightMemory,
    bank_id: str = "incidents",
    service: str | None = None,
) -> dict:
    """
    Retrieve real Hindsight memories for inspection.

    Args:
        memory: The HindsightMemory wrapper instance.
        bank_id: Hindsight bank name.
        service: Optional filter by service name.

    Returns:
        Structured memory list dictionary.
    """
    try:
        await memory.ensure_bank(bank_id)

        query_text = f"incidents, runbooks, and resolutions for {service}" if service else "all incident memories and resolutions"
        raw_recall = await memory.recall(bank_id=bank_id, query=query_text)
        text = str(raw_recall).strip()

        if not text or text.lower() in ("none", "null", ""):
            return {
                "bank_id": bank_id,
                "service_filter": service,
                "total_memories": 0,
                "memories": [],
                "status": "empty",
                "message": "No memories found in Hindsight bank.",
            }

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        memories = []

        for idx, para in enumerate(paragraphs):
            # Simple metadata extraction from structured memory blocks
            context = "incident_resolution" if "[INCIDENT RESOLUTION]" in para else "general_memory"
            extracted_svc = service
            if "Service       :" in para:
                for line in para.split("\n"):
                    if "Service       :" in line:
                        extracted_svc = line.split(":", 1)[1].strip()

            if service and extracted_svc and service.lower() not in extracted_svc.lower():
                continue

            memories.append({
                "id": f"mem-{idx+1}",
                "content": para,
                "context": context,
                "service": extracted_svc or "general",
                "is_hindsight_native": True,
            })

        return {
            "bank_id": bank_id,
            "service_filter": service,
            "total_memories": len(memories),
            "memories": memories,
            "status": "ok",
        }

    except (HindsightMemoryError, Exception) as exc:
        logger.warning("F9 Memory Inspector failed: %s", exc)
        return {
            "bank_id": bank_id,
            "service_filter": service,
            "total_memories": 0,
            "memories": [],
            "status": "degraded",
            "warning": f"Hindsight memory unavailable: {exc}",
        }
