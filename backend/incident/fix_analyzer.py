"""
backend/incident/fix_analyzer.py
---------------------------------
F4 — Known-Bad Fix Avoidance.

Inspects recalled runbook-outcome memories and flags fixes that have
historically failed so the diagnosis can list them under "Do Not Try".

Design rules:
  • Evidence MUST come from recalled Hindsight memories — never invented.
  • Detection is deterministic: we scan for explicit failure markers in
    memory text rather than asking the LLM to guess.
  • Mixed-results fixes (failed once but succeeded more times) are labelled
    "Mixed results" but are NOT banned.
  • Only runbook-outcome memories are scanned (query_label = "runbook-outcome"),
    though any memory with failure keywords counts as supporting evidence.
"""

from __future__ import annotations

import logging
import re

from backend.incident.models import (
    FixAnalysisResult,
    KnownBadFix,
    RecallPlannerResult,
)

logger = logging.getLogger(__name__)

# ── Failure / success signal patterns ────────────────────────────────────────

_FAILURE_RE = re.compile(
    r"\b(failed|failure|did not work|unsuccessful|made it worse|caused outage|"
    r"rollback|reverted|broke|worsened|no effect|ineffective|do not use|"
    r"do not try|avoid|not recommended)\b",
    re.IGNORECASE,
)

_SUCCESS_RE = re.compile(
    r"\b(succeeded|worked|resolved|fixed|successful|effective|recommended|"
    r"applied successfully|confirmed working)\b",
    re.IGNORECASE,
)

# Patterns that indicate an action/fix is being described
_FIX_CONTEXT_RE = re.compile(
    r"\b(runbook|fix|patch|restart|rollback|increase|decrease|disable|enable|"
    r"update|deploy|scale|migrate|reconfigure|flush|clear|rotate|reboot)\b",
    re.IGNORECASE,
)


def _count_matches(pattern: re.Pattern, text: str) -> int:
    return len(pattern.findall(text))


def _extract_fix_description(text: str) -> str:
    """Pull the most fix-like sentence from a memory text."""
    sentences = re.split(r"[.!?\n]", text)
    # Prefer sentences that mention an action
    for s in sentences:
        if _FIX_CONTEXT_RE.search(s) and len(s.strip()) > 10:
            return s.strip()[:200]
    # Fall back to first non-empty sentence
    for s in sentences:
        if s.strip():
            return s.strip()[:200]
    return text[:200]


def _extract_failure_reason(text: str) -> str:
    """Extract the failure sentence from a memory."""
    sentences = re.split(r"[.!?\n]", text)
    for s in sentences:
        if _FAILURE_RE.search(s) and len(s.strip()) > 5:
            return s.strip()[:300]
    return "Historical evidence indicates this fix was unsuccessful."


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_known_bad_fixes(recall: RecallPlannerResult) -> FixAnalysisResult:
    """
    Scan recalled memories for historically-failed fixes.

    Args:
        recall: The F2 RecallPlannerResult containing recalled memories.

    Returns:
        FixAnalysisResult — always valid, never raises.

    Evidence rule: A fix is marked known-bad only when a recalled memory
    explicitly contains failure-signal keywords AND describes an action/fix.
    A memory that records both failures AND successes → mixed_results=True.
    """
    if not recall.memories:
        return FixAnalysisResult(analysis_skipped=True)

    known_bad: list[KnownBadFix] = []
    mixed: list[KnownBadFix] = []

    for mem in recall.memories:
        text = mem.text

        failure_count = _count_matches(_FAILURE_RE, text)
        success_count = _count_matches(_SUCCESS_RE, text)
        has_fix_context = bool(_FIX_CONTEXT_RE.search(text))

        if failure_count == 0 or not has_fix_context:
            # No failure evidence — skip
            continue

        fix_desc    = _extract_fix_description(text)
        fail_reason = _extract_failure_reason(text)

        entry = KnownBadFix(
            fix_description   = fix_desc,
            failure_reason    = fail_reason,
            evidence_text     = text,
            query_label       = mem.query_label,
            memory_id         = mem.memory_id,
            mixed_results     = success_count > 0,
            safer_alternative = "",
        )

        if success_count > failure_count:
            # Succeeded more than it failed → mixed (not banned)
            entry = entry.model_copy(update={"mixed_results": True})
            mixed.append(entry)
            logger.debug("F4: Mixed-results fix detected: %s", fix_desc[:60])
        elif failure_count > 0:
            known_bad.append(entry)
            logger.info("F4: Known-bad fix detected: %s", fix_desc[:60])

    return FixAnalysisResult(
        known_bad_fixes    = known_bad,
        mixed_result_fixes = mixed,
        analysis_skipped   = False,
    )
