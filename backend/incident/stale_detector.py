"""
backend/incident/stale_detector.py
------------------------------------
F5 — Outdated-Fix Detection.

Compares current incident context (service version, environment, deployment)
against contextual signals extracted from recalled memories to flag fixes
that may no longer be valid.

Design rules:
  • Never claim a fix is definitely obsolete without evidence.
  • Use qualified language: "potentially outdated", "requires verification".
  • Contextual difference is detected deterministically from text patterns.
  • The LLM is NOT called here — pure string analysis.
"""

from __future__ import annotations

import logging
import re

from backend.incident.models import (
    NormalizedAlert,
    OutdatedFixAssessment,
    RecallPlannerResult,
    StaleDetectionResult,
)

logger = logging.getLogger(__name__)

# ── Patterns for extracting context from memory text ─────────────────────────

_VERSION_RE = re.compile(
    r"\b(?:version|v|ver|release|tag)\s*[:\-=]?\s*"
    r"(?P<ver>[0-9]+\.[0-9]+(?:\.[0-9]+)?(?:[-_][a-zA-Z0-9]+)?)",
    re.IGNORECASE,
)

_ENV_RE = re.compile(
    r"\b(?:environment|env)\s*[:\-=]?\s*"
    r"(?P<env>production|prod|staging|stage|dev|development|test|qa)\b",
    re.IGNORECASE,
)

_DEPLOY_RE = re.compile(
    r"\b(?:deploy(?:ment)?|release|rollout|build)\s*[:\-=]?\s*"
    r"(?P<dep>[a-zA-Z0-9_\-\.]{4,40})\b",
    re.IGNORECASE,
)

# Staleness signal words in memory
_STALE_SIGNALS_RE = re.compile(
    r"\b(deprecated|removed|replaced|migrated|upgraded|changed|"
    r"no longer|obsolete|discontinued|renamed|dropped)\b",
    re.IGNORECASE,
)

# Fix-describing sentences
_FIX_SENTENCE_RE = re.compile(
    r"\b(fix|runbook|resolution|solution|workaround|patch|restart|"
    r"increase|decrease|disable|enable|update|deploy|reconfigure)\b",
    re.IGNORECASE,
)


def _extract_version(text: str) -> str:
    m = _VERSION_RE.search(text)
    return m.group("ver") if m else ""


def _extract_env(text: str) -> str:
    m = _ENV_RE.search(text)
    return m.group("env") if m else ""


def _extract_fix_sentence(text: str) -> str:
    for sentence in re.split(r"[.!\n]", text):
        if _FIX_SENTENCE_RE.search(sentence) and len(sentence.strip()) > 10:
            return sentence.strip()[:200]
    return text[:200]


def _build_current_context(
    alert: NormalizedAlert,
    service_version: str,
    environment: str,
    deployment_id: str,
) -> str:
    parts = [f"service={alert.service}"]
    if service_version:
        parts.append(f"version={service_version}")
    if environment:
        parts.append(f"environment={environment}")
    if deployment_id:
        parts.append(f"deployment={deployment_id}")
    return ", ".join(parts)


def _compare_context(
    historical_text: str,
    current_service_version: str,
    current_environment: str,
    current_deployment: str,
) -> tuple[list[str], str]:
    """
    Compare historical memory context with current incident context.

    Returns:
        (differences, status)
        status: "potentially_outdated" | "requires_verification" | "likely_valid"
    """
    differences: list[str] = []

    # Check explicit staleness language in the memory
    stale_hits = _STALE_SIGNALS_RE.findall(historical_text)
    if stale_hits:
        differences.append(
            f"Historical memory contains staleness signals: {', '.join(set(stale_hits))}"
        )

    # Version comparison
    hist_version = _extract_version(historical_text)
    if hist_version and current_service_version:
        if hist_version != current_service_version:
            differences.append(
                f"Historical service version '{hist_version}' differs "
                f"from current '{current_service_version}'"
            )

    # Environment comparison
    hist_env = _extract_env(historical_text)
    if hist_env and current_environment:
        if hist_env.lower() != current_environment.lower():
            differences.append(
                f"Historical environment '{hist_env}' differs "
                f"from current '{current_environment}'"
            )

    if not differences:
        return [], "likely_valid"

    # Classify severity of staleness
    if stale_hits or (hist_version and current_service_version and hist_version != current_service_version):
        status = "potentially_outdated"
    else:
        status = "requires_verification"

    return differences, status


# ── Public API ────────────────────────────────────────────────────────────────

def detect_stale_fixes(
    alert: NormalizedAlert,
    recall: RecallPlannerResult,
    service_version: str = "",
    environment: str = "",
    deployment_id: str = "",
) -> StaleDetectionResult:
    """
    Scan recalled memories for fixes that may be outdated given the current
    incident context.

    Args:
        alert:           The normalized alert (provides current service name).
        recall:          F2 result containing recalled memories.
        service_version: Current service version string (from DiagnoseRequest).
        environment:     Current environment (from DiagnoseRequest).
        deployment_id:   Current deployment ID (from DiagnoseRequest).

    Returns:
        StaleDetectionResult — always valid, never raises.
    """
    if not recall.memories:
        return StaleDetectionResult(analysis_skipped=True)

    # Only assess memories that describe a fix/runbook
    candidate_memories = [
        m for m in recall.memories
        if _FIX_SENTENCE_RE.search(m.text)
    ]

    if not candidate_memories:
        logger.debug("F5: No fix-describing memories found — skipping stale detection.")
        return StaleDetectionResult(analysis_skipped=True)

    current_ctx_str = _build_current_context(
        alert, service_version, environment, deployment_id
    )

    assessments: list[OutdatedFixAssessment] = []

    for mem in candidate_memories:
        hist_ctx = (
            f"service={alert.service}"
            + (f", version={_extract_version(mem.text)}" if _extract_version(mem.text) else "")
            + (f", environment={_extract_env(mem.text)}" if _extract_env(mem.text) else "")
        )

        differences, status = _compare_context(
            mem.text,
            service_version,
            environment,
            deployment_id,
        )

        if status == "likely_valid":
            continue

        fix_desc = _extract_fix_sentence(mem.text)
        reason = (
            "Historical fix was applied in a different context — "
            "verify it still applies before executing."
        ) if not differences else " | ".join(differences)

        assessments.append(
            OutdatedFixAssessment(
                fix_description   = fix_desc,
                historical_context = hist_ctx,
                current_context   = current_ctx_str,
                differences       = differences,
                status            = status,
                reason            = reason,
                evidence_text     = mem.text,
                memory_id         = mem.memory_id,
            )
        )
        logger.info("F5: Stale fix flagged (%s): %s", status, fix_desc[:60])

    return StaleDetectionResult(assessments=assessments, analysis_skipped=False)
