"""
backend/incident/recall_planner.py
-----------------------------------
F2 — Memory-Backed Recall Planner.

For every normalized alert, fires FOUR targeted Hindsight recall queries:

  Q1 — Similar symptoms on this service
  Q2 — Root causes associated with the error signature
  Q3 — Runbooks that succeeded or failed for this situation
  Q4 — Recent infrastructure/deployment changes affecting the service

Design rules:
  • Always uses the existing HindsightMemory wrapper — never calls the
    Hindsight SDK directly.
  • Deduplicates near-identical memory texts (Jaccard similarity > 0.85).
  • Caps results at MAX_MEMORIES per query (default 5).
  • If Hindsight is unavailable the planner returns an empty result so
    the caller can continue in no-memory mode (F13).
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher

from backend.incident.models import NormalizedAlert, RecallPlannerResult, RecalledMemory
from backend.memory.hindsight import HindsightMemory, HindsightMemoryError

logger = logging.getLogger(__name__)

MAX_MEMORIES_PER_QUERY = 5
DEDUP_THRESHOLD        = 0.85   # Jaccard / SequenceMatcher ratio

# ── Query templates ───────────────────────────────────────────────────────────

def _build_queries(alert: NormalizedAlert) -> list[tuple[str, str]]:
    """
    Build the four recall queries for a normalised alert.

    Returns:
        List of (query_text, human_readable_label) tuples.
    """
    service = alert.service
    sig     = alert.error_signature

    return [
        (
            f"incidents and errors on {service} with similar symptoms: {alert.summary}",
            "similar-symptoms",
        ),
        (
            f"root causes and diagnoses for: {sig}",
            "root-cause",
        ),
        (
            f"runbooks and fixes that succeeded or failed for {service} error: {sig}",
            "runbook-outcome",
        ),
        (
            f"infrastructure changes, deployments, or configuration updates affecting {service}",
            "infra-change",
        ),
    ]


# ── Deduplication ────────────────────────────────────────────────────────────

def _similar(a: str, b: str) -> float:
    """Fast approximate string similarity in [0, 1]."""
    return SequenceMatcher(None, a[:500], b[:500]).ratio()


def _deduplicate(memories: list[RecalledMemory]) -> list[RecalledMemory]:
    """
    Remove near-duplicate memory texts (ratio > DEDUP_THRESHOLD).
    Keeps the first occurrence.
    """
    seen: list[str] = []
    unique: list[RecalledMemory] = []
    for mem in memories:
        if any(_similar(mem.text, s) > DEDUP_THRESHOLD for s in seen):
            logger.debug("Deduplication: dropped near-duplicate memory.")
            continue
        seen.append(mem.text)
        unique.append(mem)
    return unique


# ── Hindsight recall helper ───────────────────────────────────────────────────

async def _recall_one(
    memory: HindsightMemory,
    bank_id: str,
    query: str,
    label: str,
) -> list[RecalledMemory]:
    """
    Run a single recall query and parse the result into RecalledMemory objects.

    Hindsight's arecall returns a string or an object with a results attribute.
    We handle both shapes defensively.
    """
    try:
        raw = await memory.recall(bank_id=bank_id, query=query)
        text = str(raw).strip()
        if not text or text.lower() in ("none", "null", ""):
            return []

        # Some Hindsight versions return structured objects; try to extract items.
        # If the wrapper already stringifies, we get one block of text.
        # Treat each paragraph as a separate memory item.
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        results = []
        for para in paragraphs[:MAX_MEMORIES_PER_QUERY]:
            results.append(
                RecalledMemory(
                    text        = para,
                    query       = query,
                    query_label = label,
                    memory_id   = "",
                )
            )
        return results

    except HindsightMemoryError as exc:
        logger.warning("Recall query '%s' failed: %s", label, exc)
        return []


# ── Public API ────────────────────────────────────────────────────────────────

async def plan_recall(
    alert: NormalizedAlert,
    memory: HindsightMemory,
    bank_id: str,
) -> RecallPlannerResult:
    """
    Execute the four recall queries for the alert and return a deduplicated
    RecallPlannerResult.

    Args:
        alert:   The normalized alert (F1 output).
        memory:  The existing HindsightMemory wrapper instance.
        bank_id: The Hindsight bank to query (e.g. service name or "incidents").

    Returns:
        RecallPlannerResult with memories, queries, and used_memory flag.

    Never raises — on Hindsight failure returns an empty result so the
    pipeline continues in no-memory mode (F13 resilience).
    """
    # Ensure the bank exists before querying
    try:
        await memory.ensure_bank(bank_id)
    except HindsightMemoryError as exc:
        logger.warning("Could not ensure Hindsight bank '%s': %s", bank_id, exc)
        return RecallPlannerResult(memories=[], queries=[], used_memory=False)

    queries = _build_queries(alert)
    all_memories: list[RecalledMemory] = []

    for query_text, label in queries:
        items = await _recall_one(memory, bank_id, query_text, label)
        all_memories.extend(items)
        logger.debug("Query '%s' returned %d items.", label, len(items))

    # Deduplicate across queries
    unique_memories = _deduplicate(all_memories)

    used_memory = len(unique_memories) > 0

    return RecallPlannerResult(
        memories    = unique_memories,
        queries     = [q for q, _ in queries],
        used_memory = used_memory,
    )
