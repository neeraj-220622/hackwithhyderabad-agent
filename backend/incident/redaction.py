"""
backend/incident/redaction.py
-----------------------------
F14 — Redaction and Safety Filter.

RULE: Every string destined for Hindsight RETAIN must pass through
      `redact()` before being stored. Nothing that bypasses this
      function should ever be retained.

Detected and replaced:
  • API keys / bearer tokens
  • Passwords (URL-embedded and key=value patterns)
  • E-mail addresses
  • IPv4 addresses (when REDACT_IPS=true, default off for internal tooling)
  • Customer / tenant identifiers (UUID-shaped values)

Placeholders used:
  <REDACTED_TOKEN>
  <REDACTED_PASSWORD>
  <REDACTED_EMAIL>
  <REDACTED_IP>
  <REDACTED_ID>

Only redaction *counts* are logged — original secrets are never logged.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


# ── Patterns ──────────────────────────────────────────────────────────────────
#
# Each entry: (compiled_regex, replacement_placeholder)
# Ordered from most-specific to least-specific to avoid partial matches.

_BEARER_RE   = re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]{20,}={0,2}", re.IGNORECASE)
_TOKEN_RE    = re.compile(
    r"""(?xi)
    (?:
        api[_\-]?key   |
        auth[_\-]?token |
        access[_\-]?token |
        secret[_\-]?key |
        x\-api\-key
    )
    \s*[=:]\s*
    ['"]?
    ([A-Za-z0-9\-._~+/]{16,})
    ['"]?
    """,
    re.IGNORECASE,
)
_PASSWORD_RE = re.compile(
    r"""(?xi)
    (?:password|passwd|pwd)
    \s*[=:]\s*
    ['"]?
    (\S{6,})
    ['"]?
    """,
    re.IGNORECASE,
)
_URL_CREDS_RE = re.compile(
    r"(?P<scheme>[a-z][a-z0-9+\-.]*://)(?P<creds>[^@/\s]{4,}@)",
    re.IGNORECASE,
)
_EMAIL_RE    = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_IPV4_RE     = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)
_UUID_RE     = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


def redact(text: str, *, redact_ips: bool = False, redact_uuids: bool = False) -> str:
    """
    Scan *text* and replace detected secrets with safe placeholders.

    Args:
        text:         The string to sanitise.
        redact_ips:   Replace IPv4 addresses when True (default False — internal
                      tooling often uses IP addresses that are not sensitive).
        redact_uuids: Replace UUID-shaped customer/tenant IDs when True.

    Returns:
        Sanitised string. If no sensitive data is found the original string is
        returned unchanged (same object, no allocation).
    """
    if not text:
        return text

    counts: dict[str, int] = {}

    def _sub(pattern: re.Pattern, placeholder: str, t: str) -> str:
        result, n = pattern.subn(placeholder, t)
        if n:
            counts[placeholder] = counts.get(placeholder, 0) + n
        return result

    # Order matters — tokens before passwords to avoid double-hitting.
    text = _BEARER_RE.sub("<REDACTED_TOKEN>", text)
    text = _TOKEN_RE.sub(lambda m: m.group(0).split("=")[0].split(":")[0] + "=<REDACTED_TOKEN>", text)
    text = _PASSWORD_RE.sub(lambda m: m.group(0).split("=")[0].split(":")[0] + "=<REDACTED_PASSWORD>", text)
    text = _URL_CREDS_RE.sub(r"\g<scheme><REDACTED_PASSWORD>@", text)
    text = _sub(_EMAIL_RE, "<REDACTED_EMAIL>", text)

    if redact_ips:
        text = _sub(_IPV4_RE, "<REDACTED_IP>", text)
    if redact_uuids:
        text = _sub(_UUID_RE, "<REDACTED_ID>", text)

    if counts:
        logger.info("Redaction applied: %s", counts)

    return text


def redact_alert_fields(
    raw_text: str,
    logs: str = "",
    *,
    redact_ips: bool = False,
) -> tuple[str, str]:
    """
    Convenience wrapper: redact both the alert text and log excerpt.

    Returns:
        (redacted_alert_text, redacted_logs)
    """
    return redact(raw_text, redact_ips=redact_ips), redact(logs, redact_ips=redact_ips)
