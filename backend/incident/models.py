"""
backend/incident/models.py
--------------------------
Pydantic models for the full incident lifecycle.

These are the canonical data shapes shared across all incident modules.
Future slices (F4–F13) extend DiagnosisResult / IncidentRecord without
breaking existing callers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    UNKNOWN  = "unknown"


class IncidentStatus(str, Enum):
    OPEN       = "open"
    DIAGNOSED  = "diagnosed"
    RESOLVED   = "resolved"


class MemoryCategory(str, Enum):
    """Labels used when retaining memories in Hindsight (F7, F6, F8)."""
    INCIDENT_RESOLUTION  = "incident resolution"
    RUNBOOK_OUTCOME      = "runbook outcome"
    ENGINEER_FEEDBACK    = "engineer feedback"
    INFRASTRUCTURE_CHANGE = "infrastructure change"
    POST_MORTEM          = "post-mortem"


# ── F1 – Normalised alert ─────────────────────────────────────────────────────

class NormalizedAlert(BaseModel):
    """Output of F1 Alert Intake and Normalization."""
    service: str = Field(..., description="Service/system name, e.g. 'payments-api'.")
    summary: str = Field(..., description="One-sentence description of the incident.")
    error_signature: str = Field(
        ...,
        description=(
            "Stable fingerprint derived from the most distinctive log line. "
            "Timestamps, pod names, and IDs are stripped so the same underlying "
            "error always maps to the same signature."
        ),
    )
    severity: Severity = Field(Severity.UNKNOWN, description="Estimated severity level.")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the alert was first observed (UTC).",
    )
    logs_trimmed: str = Field("", description="Relevant log excerpt around first error.")
    raw_text: str = Field("", description="Original free-text alert as received.")
    service_inferred: bool = Field(
        False,
        description="True when the service name was extracted rather than explicitly supplied.",
    )


# ── F2 – Recall planner output ────────────────────────────────────────────────

class RecalledMemory(BaseModel):
    """One item returned by the Hindsight recall planner."""
    text: str           = Field(..., description="Raw memory text from Hindsight.")
    query: str          = Field(..., description="The query that retrieved this memory.")
    query_label: str    = Field("", description="Human-readable label for the query type.")
    memory_id: str      = Field("", description="Hindsight memory ID if available.")


class RecallPlannerResult(BaseModel):
    """Output of F2 Memory-Backed Recall Planner."""
    memories: list[RecalledMemory] = Field(default_factory=list)
    queries: list[str]             = Field(default_factory=list)
    used_memory: bool              = Field(False)


# ── F3 – Diagnosis ────────────────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    """A single piece of evidence backing a hypothesis."""
    memory_text: str  = Field(..., description="Exact text of the recalled memory used.")
    query_label: str  = Field("", description="Which recall query surfaced this memory.")
    memory_id: str    = Field("", description="Hindsight memory ID if available.")


class Hypothesis(BaseModel):
    """One root-cause hypothesis produced by F3."""
    root_cause: str                   = Field(..., description="Proposed root cause.")
    confidence: float                 = Field(..., ge=0.0, le=1.0, description="0–1 confidence.")
    evidence: list[EvidenceItem]      = Field(default_factory=list)
    outdated_warning: str             = Field(
        "",
        description="Set by F5 when a fix this hypothesis implies may be stale.",
    )


class DiagnosisResult(BaseModel):
    """Output of F3 Evidence-Cited Diagnosis."""
    incident_id: str                  = Field(default_factory=lambda: str(uuid4()))
    hypotheses: list[Hypothesis]      = Field(default_factory=list)
    recommended_steps: list[str]      = Field(default_factory=list)
    avoid: list[str]                  = Field(default_factory=list)
    used_memory: bool                 = Field(False)
    memory_warning: str               = Field(
        "",
        description="Non-empty when Hindsight was unavailable (F13 no-memory mode).",
    )
    generic_diagnosis: bool           = Field(
        False,
        description="True when there was no relevant Hindsight memory to cite.",
    )


# ── F4 – Known-bad fix analysis ───────────────────────────────────────────────

class KnownBadFix(BaseModel):
    """A fix flagged by F4 as historically failed."""
    fix_description: str  = Field(..., description="The candidate fix or runbook step.")
    failure_reason: str   = Field(..., description="Why this fix is considered bad.")
    evidence_text: str    = Field(..., description="Exact recalled memory text that supports this.")
    query_label: str      = Field("", description="Which recall query surfaced the evidence.")
    memory_id: str        = Field("", description="Hindsight memory ID if available.")
    mixed_results: bool   = Field(
        False,
        description="True when the fix sometimes succeeded — labelled 'Mixed results'.",
    )
    safer_alternative: str = Field("", description="Safer alternative when available.")


class FixAnalysisResult(BaseModel):
    """Output of F4 — Known-Bad Fix Avoidance."""
    known_bad_fixes: list[KnownBadFix]  = Field(default_factory=list)
    mixed_result_fixes: list[KnownBadFix] = Field(default_factory=list)
    analysis_skipped: bool              = Field(
        False,
        description="True when Hindsight was unavailable or no runbook memories found.",
    )


# ── F5 – Outdated-fix assessment ──────────────────────────────────────────────

class OutdatedFixAssessment(BaseModel):
    """One potentially outdated fix flagged by F5."""
    fix_description: str     = Field(..., description="The historical fix being assessed.")
    historical_context: str  = Field(..., description="Context at time of original fix.")
    current_context: str     = Field(..., description="Current incident context.")
    differences: list[str]   = Field(default_factory=list, description="Detected context differences.")
    status: str              = Field(
        "potentially_outdated",
        description="One of: potentially_outdated | requires_verification | likely_valid",
    )
    reason: str              = Field(..., description="Human-readable staleness rationale.")
    evidence_text: str       = Field("", description="The recalled memory text that contained the fix.")
    memory_id: str           = Field("", description="Hindsight memory ID if available.")


class StaleDetectionResult(BaseModel):
    """Output of F5 — Outdated-Fix Detection."""
    assessments: list[OutdatedFixAssessment] = Field(default_factory=list)
    analysis_skipped: bool                   = Field(False)


# ── F6 – Engineer feedback ────────────────────────────────────────────────────

class FeedbackType(str, Enum):
    ACCEPTED  = "accepted"
    REJECTED  = "rejected"
    CORRECTED = "corrected"


class EngineerFeedback(BaseModel):
    """Structured feedback submitted by an engineer (F6)."""
    incident_id: str        = Field(..., description="The incident this feedback relates to.")
    engineer_id: str        = Field(..., min_length=1, description="Simple engineer identifier.")
    feedback_type: FeedbackType = Field(..., description="accepted | rejected | corrected")
    comment: str            = Field("", description="Free-text comment from the engineer.")
    corrected_action: str   = Field(
        "",
        description="The correct action or root cause, supplied when feedback_type=corrected.",
    )
    timestamp: datetime     = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeedbackRequest(BaseModel):
    """Request body for POST /api/incidents/{incident_id}/feedback."""
    engineer_id: str        = Field(..., min_length=1)
    feedback_type: FeedbackType
    comment: str            = Field("")
    corrected_action: str   = Field("")


class FeedbackResponse(BaseModel):
    """Response body for POST /api/incidents/{incident_id}/feedback."""
    incident_id: str
    feedback_accepted: bool
    message: str


# ── F7 – Incident closure ─────────────────────────────────────────────────────

class ClosureOutcome(str, Enum):
    RESOLVED    = "resolved"
    UNRESOLVED  = "unresolved"
    ESCALATED   = "escalated"


class ClosureRequest(BaseModel):
    """Request body for POST /api/incidents/{incident_id}/close."""
    engineer_id: str          = Field(..., min_length=1)
    final_diagnosis: str      = Field(..., min_length=1, description="Engineer's confirmed diagnosis.")
    resolution_action: str    = Field(..., min_length=1, description="What was done to resolve it.")
    outcome: ClosureOutcome   = Field(ClosureOutcome.RESOLVED)
    resolution_success: bool  = Field(True, description="Whether the resolution fully succeeded.")
    notes: str                = Field("", description="Additional context for future incidents.")


class MemoryWritebackStatus(BaseModel):
    attempted: bool = False
    succeeded: bool = False
    error: str      = ""


class ClosureResponse(BaseModel):
    """Response body for POST /api/incidents/{incident_id}/close."""
    incident_id: str
    status: str
    memory_writeback: MemoryWritebackStatus


# ── Full incident record (used by F7 closure + lightweight store) ─────────────

class IncidentRecord(BaseModel):
    """
    Full incident lifecycle record.

    Used as the lightweight in-process store until a real DB is wired in.
    Serialisable to JSON so it can be persisted to a file if needed.
    """
    incident_id: str               = Field(default_factory=lambda: str(uuid4()))
    service: str                   = ""
    summary: str                   = ""
    error_signature: str           = ""
    severity: Severity             = Severity.UNKNOWN
    started_at: datetime           = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: IncidentStatus         = IncidentStatus.OPEN

    # Raw inputs
    logs: str                      = ""
    metrics: str                   = ""

    # Derived — Slice 1
    alert: NormalizedAlert | None          = None
    recall: RecallPlannerResult | None     = None
    diagnosis: DiagnosisResult | None      = None

    # Derived — Slice 2
    fix_analysis: FixAnalysisResult | None      = None
    stale_detection: StaleDetectionResult | None = None

    # Timeline entries
    timeline: list[str]            = Field(default_factory=list)

    # Feedback items (F6) — stored as EngineerFeedback dicts
    feedback: list[dict[str, Any]] = Field(default_factory=list)

    # Resolution (F7)
    resolution: str                = ""
    resolved_at: datetime | None   = None
    closure_request: dict[str, Any] | None = None

    # Metadata
    created_at: datetime           = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime           = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── API request / response shapes ─────────────────────────────────────────────

class DiagnoseRequest(BaseModel):
    """Request body for POST /api/alerts/diagnose."""
    alert_text: str   = Field(..., min_length=1, description="Free-text alert or log paste.")
    service: str      = Field("",  description="Optional service name hint.")
    logs: str         = Field("",  description="Optional raw log excerpt.")
    metrics: str      = Field("",  description="Optional metrics summary.")
    bank_id: str      = Field("incidents", description="Hindsight bank to use for this service.")
    # Slice 2: optional context fields used by F5
    service_version: str   = Field("", description="Current service version (used by F5).")
    environment: str       = Field("", description="Current environment, e.g. production/staging.")
    deployment_id: str     = Field("", description="Current deployment identifier.")


class DiagnoseResponse(BaseModel):
    """Response body for POST /api/alerts/diagnose."""
    incident_id: str
    alert: NormalizedAlert
    recall: RecallPlannerResult
    diagnosis: DiagnosisResult
    # Slice 2 additions — always present, may be empty
    fix_analysis: FixAnalysisResult       = Field(default_factory=FixAnalysisResult)
    stale_detection: StaleDetectionResult = Field(default_factory=StaleDetectionResult)
