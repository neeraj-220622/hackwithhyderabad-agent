"""
backend/incident/patterns.py
-----------------------------
F8 — Pattern Digest using Hindsight Reflect.

Uses Hindsight memory recall/reflect to surface recurring incident patterns
for a service or across all historical incidents in a bank.
"""

from __future__ import annotations

import logging
from backend.memory.hindsight import HindsightMemory, HindsightMemoryError
from backend.incident.models import RecalledMemory

logger = logging.getLogger(__name__)


async def get_pattern_digest(
    memory: HindsightMemory,
    service: str | None = None,
    bank_id: str = "incidents",
) -> dict:
    """
    Generate an operational pattern digest from historical incident memories in Hindsight.

    Returns:
        Structured pattern digest dictionary.
    """
    try:
        # Check bank readiness
        await memory.ensure_bank(bank_id)

        # Build query for pattern reflection
        query_text = (
            f"recurring incident patterns, root causes, successful resolutions, and failed fixes for {service}"
            if service
            else "recurring incident patterns, common root causes, successful resolutions, and failed fixes across all services"
        )

        raw_recall = await memory.recall(bank_id=bank_id, query=query_text)
        text = str(raw_recall).strip()

        if not text or text.lower() in ("none", "null", ""):
            return {
                "patterns": [],
                "summary": "No historical incident patterns found in memory yet. Seed or close incidents to generate patterns.",
                "generated_from_memory": False,
                "service": service,
                "status": "empty",
            }

        # Parse memory blocks and categorize patterns
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        recurring_services: set[str] = set()
        recurring_signatures: set[str] = set()
        successful_resolutions: list[str] = []
        known_failed_approaches: list[str] = []
        patterns_list: list[dict] = []

        for p in paragraphs:
            lines = p.split("\n")
            svc = service or "Unknown Service"
            for line in lines:
                if line.startswith("Service") and ":" in line:
                    svc = line.split(":", 1)[1].strip()
                    recurring_services.add(svc)
                elif line.startswith("Error Sig") and ":" in line:
                    recurring_signatures.add(line.split(":", 1)[1].strip())
                elif line.startswith("Resolution Action") and ":" in line:
                    successful_resolutions.append(line.split(":", 1)[1].strip())
                elif ("failed" in line.lower() or "did not address" in line.lower()) and "-" in line:
                    known_failed_approaches.append(line.strip(" -"))

            patterns_list.append({
                "service": svc,
                "snippet": p[:200] + ("..." if len(p) > 200 else ""),
            })

        summary_text = (
            f"Analyzed {len(paragraphs)} historical incident records from Hindsight bank '{bank_id}'. "
            f"Identified {len(recurring_services or [service])} affected services, "
            f"{len(successful_resolutions)} verified resolution patterns, and "
            f"{len(known_failed_approaches)} recorded failed fix patterns."
        )

        return {
            "patterns": patterns_list,
            "summary": summary_text,
            "recurring_services": list(recurring_services),
            "recurring_signatures": list(recurring_signatures),
            "successful_resolutions": successful_resolutions[:5],
            "known_failed_approaches": known_failed_approaches[:5],
            "generated_from_memory": True,
            "service": service,
            "status": "ok",
        }

    except (HindsightMemoryError, Exception) as exc:
        logger.warning("F8 Pattern Digest failed: %s", exc)
        return {
            "patterns": [],
            "summary": "Historical memory temporarily unavailable — unable to generate pattern digest.",
            "generated_from_memory": False,
            "service": service,
            "status": "degraded",
            "warning": str(exc),
        }
