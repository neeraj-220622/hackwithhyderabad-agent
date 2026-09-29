"""
backend/incident/feedback.py
-----------------------------
F6 — Engineer Feedback Loop.

Provides a structured mechanism for engineers to submit feedback on the
agent's diagnosis.  Feedback is:
  1. Validated by Pydantic.
  2. Attached to the in-process IncidentRecord.
  3. Retained in Hindsight with context="engineer feedback" so future
     incidents can recall it.

Supported feedback types: accepted | rejected | corrected

All Hindsight retains run through F14 redaction first.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.incident.models import (
    EngineerFeedback,
    FeedbackRequest,
    IncidentRecord,
    MemoryCategory,
)
from backend.incident.redaction import redact
from backend.memory.hindsight import HindsightMemory, HindsightMemoryError

logger = logging.getLogger(__name__)


def build_feedback_object(
    incident_id: str,
    request: FeedbackRequest,
) -> EngineerFeedback:
    """Convert a FeedbackRequest into a validated EngineerFeedback object."""
    return EngineerFeedback(
        incident_id      = incident_id,
        engineer_id      = request.engineer_id,
        feedback_type    = request.feedback_type,
        comment          = request.comment,
        corrected_action = request.corrected_action,
        timestamp        = datetime.now(timezone.utc),
    )


def attach_feedback_to_record(
    record: IncidentRecord,
    feedback: EngineerFeedback,
) -> IncidentRecord:
    """
    Add an EngineerFeedback item to the IncidentRecord's feedback list.
    Returns a new record (Pydantic model_copy) to keep immutability.
    """
    updated_feedback = list(record.feedback) + [feedback.model_dump(mode="json")]
    return record.model_copy(
        update={
            "feedback":   updated_feedback,
            "updated_at": datetime.now(timezone.utc),
        }
    )


def _build_feedback_memory(
    record: IncidentRecord,
    feedback: EngineerFeedback,
) -> str:
    """
    Construct a self-contained memory string suitable for Hindsight RETAIN.

    The memory must be useful for future recall so it includes:
    - incident summary and error signature
    - the original hypothesis (if available)
    - engineer's feedback type and comment
    - corrected action (when provided)
    """
    diag = record.diagnosis
    hypothesis_text = ""
    if diag and diag.hypotheses:
        hypothesis_text = diag.hypotheses[0].root_cause

    parts = [
        f"[ENGINEER FEEDBACK] Service: {record.service}",
        f"Incident: {record.summary}",
        f"Error signature: {record.error_signature}",
    ]
    if hypothesis_text:
        parts.append(f"Agent hypothesis: {hypothesis_text}")

    parts.append(
        f"Engineer ({feedback.engineer_id}) feedback: {feedback.feedback_type.value}"
    )
    if feedback.comment:
        parts.append(f"Comment: {feedback.comment}")
    if feedback.corrected_action:
        parts.append(f"Corrected action: {feedback.corrected_action}")

    return "\n".join(parts)


async def retain_feedback(
    record: IncidentRecord,
    feedback: EngineerFeedback,
    memory: HindsightMemory,
    bank_id: str,
) -> tuple[bool, str]:
    """
    Retain engineer feedback into Hindsight.

    Args:
        record:   The current IncidentRecord.
        feedback: The validated EngineerFeedback.
        memory:   The existing HindsightMemory wrapper.
        bank_id:  Hindsight bank to write to.

    Returns:
        (success: bool, error_message: str)
    """
    raw_content = _build_feedback_memory(record, feedback)
    # F14 — redact before retaining
    clean_content = redact(raw_content)

    try:
        await memory.remember(
            bank_id = bank_id,
            content = clean_content,
            context = MemoryCategory.ENGINEER_FEEDBACK.value,
        )
        logger.info(
            "F6: Feedback retained for incident %s (type=%s)",
            record.incident_id, feedback.feedback_type.value,
        )
        return True, ""
    except HindsightMemoryError as exc:
        logger.error("F6: Failed to retain feedback: %s", exc)
        return False, str(exc)
