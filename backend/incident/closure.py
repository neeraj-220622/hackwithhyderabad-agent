"""
backend/incident/closure.py
----------------------------
F7 — Incident Closure and Memory Write-Back.

When an engineer resolves an incident:
  1. Validate the incident exists.
  2. Collect: diagnosis, F4 warnings, F5 stale assessments, feedback, resolution.
  3. Apply F14 redaction.
  4. Construct a self-contained structured learning memory.
  5. RETAIN it into Hindsight with context="incident resolution".
  6. Return a ClosureResponse with write-back status.

If Hindsight is unavailable the incident is still closed locally and the
response clearly reports the write-back failure.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.incident.models import (
    ClosureRequest,
    ClosureResponse,
    IncidentRecord,
    IncidentStatus,
    MemoryCategory,
    MemoryWritebackStatus,
)
from backend.incident.redaction import redact
from backend.memory.hindsight import HindsightMemory, HindsightMemoryError

logger = logging.getLogger(__name__)


def _build_resolution_memory(
    record: IncidentRecord,
    closure: ClosureRequest,
    resolved_at: datetime,
) -> str:
    """
    Construct the self-contained learning memory that will be retained
    in Hindsight.  Future incidents should be able to RECALL this and
    learn from it.

    The memory deliberately includes:
      - service + error signature (for recall matching)
      - confirmed root cause
      - resolution action and outcome
      - failed fixes (F4)
      - stale warnings (F5)
      - engineer feedback summary
      - timestamp
    """
    lines: list[str] = []

    # Header
    lines.append("[INCIDENT RESOLUTION]")
    lines.append(f"Service       : {record.service}")
    lines.append(f"Incident ID   : {record.incident_id}")
    lines.append(f"Error Sig     : {record.error_signature}")
    lines.append(f"Summary       : {record.summary}")
    lines.append(f"Severity      : {record.severity}")
    lines.append(f"Resolved At   : {resolved_at.isoformat()}")
    lines.append(f"Outcome       : {closure.outcome.value}")

    # Confirmed diagnosis
    lines.append("")
    lines.append(f"Confirmed Root Cause: {closure.final_diagnosis}")

    # Resolution
    lines.append(f"Resolution Action: {closure.resolution_action}")
    lines.append(f"Success: {closure.resolution_success}")
    if closure.notes:
        lines.append(f"Notes: {closure.notes}")

    # Failed fixes from F4
    fix = record.fix_analysis
    if fix and fix.known_bad_fixes:
        lines.append("")
        lines.append("Failed Fixes (Do Not Repeat):")
        for kbf in fix.known_bad_fixes:
            lines.append(f"  - {kbf.fix_description}: {kbf.failure_reason}")

    # Stale warnings from F5
    stale = record.stale_detection
    if stale and stale.assessments:
        lines.append("")
        lines.append("Potentially Outdated Fixes:")
        for a in stale.assessments:
            lines.append(f"  - {a.fix_description} ({a.status}): {a.reason}")

    # Engineer feedback
    if record.feedback:
        lines.append("")
        lines.append("Engineer Feedback:")
        for fb in record.feedback:
            lines.append(
                f"  [{fb.get('feedback_type', '?')}] by {fb.get('engineer_id', '?')}: "
                f"{fb.get('comment', '')} "
                f"{'| Correction: ' + fb['corrected_action'] if fb.get('corrected_action') else ''}"
            )

    return "\n".join(lines)


async def close_incident(
    record: IncidentRecord,
    closure: ClosureRequest,
    memory: HindsightMemory,
    bank_id: str,
) -> tuple[IncidentRecord, ClosureResponse]:
    """
    Close an incident and write a learning memory to Hindsight.

    Args:
        record:   The in-process IncidentRecord.
        closure:  The validated ClosureRequest from the engineer.
        memory:   The existing HindsightMemory wrapper.
        bank_id:  Hindsight bank to write to.

    Returns:
        (updated_record, ClosureResponse)

    Never raises — Hindsight failures are captured in MemoryWritebackStatus.
    """
    resolved_at = datetime.now(timezone.utc)

    # Build and redact the learning memory
    raw_memory = _build_resolution_memory(record, closure, resolved_at)
    clean_memory = redact(raw_memory)

    # Attempt Hindsight RETAIN
    writeback = MemoryWritebackStatus(attempted=True)
    try:
        await memory.remember(
            bank_id = bank_id,
            content = clean_memory,
            context = MemoryCategory.INCIDENT_RESOLUTION.value,
        )
        writeback = MemoryWritebackStatus(attempted=True, succeeded=True)
        logger.info(
            "F7: Resolution memory retained for incident %s", record.incident_id
        )
    except HindsightMemoryError as exc:
        writeback = MemoryWritebackStatus(
            attempted = True,
            succeeded = False,
            error     = str(exc),
        )
        logger.error(
            "F7: Failed to retain resolution memory for %s: %s",
            record.incident_id, exc,
        )

    # Update IncidentRecord
    updated = record.model_copy(
        update={
            "status":          IncidentStatus.RESOLVED,
            "resolution":      closure.resolution_action,
            "resolved_at":     resolved_at,
            "closure_request": closure.model_dump(mode="json"),
            "updated_at":      resolved_at,
        }
    )

    response = ClosureResponse(
        incident_id     = record.incident_id,
        status          = "closed",
        memory_writeback = writeback,
    )

    return updated, response
