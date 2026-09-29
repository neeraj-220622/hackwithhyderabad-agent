"""
backend/incident/normalizer.py
------------------------------
F1 — Alert Intake and Normalization.

Converts free-text alerts (copy-pasted from PagerDuty, Grafana, Slack, logs,
etc.) into a structured NormalizedAlert object.

Design rules:
  • This module is PURE — no LLM calls, no Hindsight calls.
  • Deterministic: the same underlying error always produces the same
    error_signature regardless of timestamps, pod names, or IDs.
  • Modular: called from IncidentResponseService, NOT from Agent.run().
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from backend.incident.models import NormalizedAlert, Severity
from backend.incident.redaction import redact_alert_fields

# ── Known services dictionary (extendable) ────────────────────────────────────

KNOWN_SERVICES: list[str] = [
    "payments-api",
    "payments",
    "auth-service",
    "auth",
    "user-service",
    "users",
    "order-service",
    "orders",
    "inventory-service",
    "inventory",
    "notification-service",
    "notifications",
    "gateway",
    "api-gateway",
    "db",
    "database",
    "redis",
    "kafka",
    "rabbitmq",
    "elasticsearch",
    "search-service",
    "frontend",
    "backend",
]

# ── Normalisation patterns ────────────────────────────────────────────────────

# Timestamps (ISO-8601, epoch, common log formats)
_TIMESTAMP_RE = re.compile(
    r"""(?x)
    \d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?  # ISO-8601
    | \b\d{10,13}\b                                                               # epoch sec/ms
    | \w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}                                        # syslog
    """
)

# Kubernetes-style pod suffixes: name-abc12-xyz34
_POD_SUFFIX_RE = re.compile(r"-[a-z0-9]{5}-[a-z0-9]{5}\b")

# Generic numeric IDs (not UUIDs — those are handled by redaction)
_NUMERIC_ID_RE = re.compile(r"\b\d{4,}\b")

# IPv4 addresses
_IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# Error-level indicators (used to score candidate log lines)
_ERROR_KEYWORDS = re.compile(
    r"\b(error|exception|fatal|panic|traceback|critical|failure|failed|timeout|refused|"
    r"denied|unavailable|crash|oom|killed|segfault)\b",
    re.IGNORECASE,
)

# Severity signals
_SEVERITY_MAP: list[tuple[re.Pattern, Severity]] = [
    (re.compile(r"\b(critical|fatal|panic|oom|killed)\b",       re.IGNORECASE), Severity.CRITICAL),
    (re.compile(r"\b(error|exception|crash|segfault)\b",        re.IGNORECASE), Severity.HIGH),
    (re.compile(r"\b(warning|warn|timeout|refused|unavailable)\b", re.IGNORECASE), Severity.MEDIUM),
    (re.compile(r"\b(info|notice|debug)\b",                     re.IGNORECASE), Severity.LOW),
]


# ── Internal helpers ──────────────────────────────────────────────────────────

def _strip_volatile_parts(line: str) -> str:
    """
    Remove the parts of a log line that change between occurrences:
    timestamps, pod IDs, numeric IDs, IP addresses.

    The result is stable across pods / restarts — same error → same signature.
    """
    line = _TIMESTAMP_RE.sub("", line)
    line = _POD_SUFFIX_RE.sub("", line)
    line = _IPV4_RE.sub("<IP>", line)
    line = _NUMERIC_ID_RE.sub("<NUM>", line)
    # Collapse extra whitespace
    line = " ".join(line.split())
    return line.strip()


def _score_line(line: str) -> int:
    """Score a log line by how many error-keyword hits it contains."""
    return len(_ERROR_KEYWORDS.findall(line))


def _extract_error_signature(logs: str, alert_text: str) -> str:
    """
    Derive a stable error_signature from the most distinctive log line.

    Falls back to stripping the alert text itself when there are no logs.
    """
    # Prefer the log excerpt; fall back to alert text
    source = logs if logs.strip() else alert_text

    lines = [l.strip() for l in source.splitlines() if l.strip()]
    if not lines:
        return "unknown-error"

    # Pick the line with the most error keyword hits; break ties by length
    best = max(lines, key=lambda l: (_score_line(l), len(l)))

    signature = _strip_volatile_parts(best)
    # Lowercase and truncate to keep it concise
    signature = signature.lower()[:200]
    return signature or "unknown-error"


def _infer_service(text: str) -> tuple[str, bool]:
    """
    Return (service_name, was_inferred) by scanning the text for known service names.
    If none are found, return ("unknown-service", True).
    """
    text_lower = text.lower()
    for svc in KNOWN_SERVICES:
        if svc in text_lower:
            return svc, True
    return "unknown-service", True


def _estimate_severity(text: str) -> Severity:
    for pattern, severity in _SEVERITY_MAP:
        if pattern.search(text):
            return severity
    return Severity.UNKNOWN


def _trim_logs(logs: str, max_lines: int = 20) -> str:
    """
    Return the log lines most relevant to the error: up to max_lines lines
    centred around the first high-scoring line.
    """
    lines = [l for l in logs.splitlines() if l.strip()]
    if not lines:
        return ""
    if len(lines) <= max_lines:
        return "\n".join(lines)

    # Find the first error line
    first_error = 0
    for i, line in enumerate(lines):
        if _score_line(line) > 0:
            first_error = i
            break

    start = max(0, first_error - 3)
    end   = min(len(lines), start + max_lines)
    return "\n".join(lines[start:end])


def _build_summary(service: str, error_sig: str, alert_text: str) -> str:
    """Produce a one-sentence summary."""
    # Try to extract the first sentence from the alert text
    first_line = next((l.strip() for l in alert_text.splitlines() if l.strip()), "")
    if first_line and len(first_line) < 200:
        return first_line
    return f"{service}: {error_sig[:100]}"


# ── Public API ────────────────────────────────────────────────────────────────

def normalize_alert(
    alert_text: str,
    service: str = "",
    logs: str = "",
    metrics: str = "",
) -> NormalizedAlert:
    """
    Convert raw alert inputs into a structured NormalizedAlert.

    Args:
        alert_text: Free-text alert (required).
        service:    Optional service name. Inferred if absent.
        logs:       Optional raw log excerpt.
        metrics:    Optional metrics summary (not used in normalisation yet).

    Returns:
        NormalizedAlert with a stable error_signature.

    Acceptance criterion:
        The same underlying error with different timestamps or pod names
        must produce the same error_signature.
    """
    if not alert_text or not alert_text.strip():
        raise ValueError("alert_text must not be empty.")

    # F14 — redact before any processing
    alert_text_clean, logs_clean = redact_alert_fields(alert_text, logs)

    service_inferred = False
    if not service or not service.strip():
        service, service_inferred = _infer_service(alert_text_clean + " " + logs_clean)
    else:
        service = service.strip()

    error_signature = _extract_error_signature(logs_clean, alert_text_clean)
    severity        = _estimate_severity(alert_text_clean + " " + logs_clean)
    logs_trimmed    = _trim_logs(logs_clean)
    summary         = _build_summary(service, error_signature, alert_text_clean)

    return NormalizedAlert(
        service          = service,
        summary          = summary,
        error_signature  = error_signature,
        severity         = severity,
        started_at       = datetime.now(timezone.utc),
        logs_trimmed     = logs_trimmed,
        raw_text         = alert_text_clean,
        service_inferred = service_inferred,
    )
