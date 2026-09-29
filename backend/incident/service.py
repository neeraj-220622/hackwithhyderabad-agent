"""
backend/incident/service.py
----------------------------
IncidentResponseService — orchestrator for the full Slice 1 + Slice 2 pipeline.

Slice 1 chain (unchanged):
  normalize_alert (F1)
  → redact (F14, inside normalizer)
  → plan_recall (F2)
  → diagnose (F3)

Slice 2 additions:
  → analyze_known_bad_fixes (F4)
  → detect_stale_fixes (F5)
  → add_feedback (F6)
  → close_incident (F7)

The generic Agent.run() is NOT touched — this service lives alongside it.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.agent.llm import LLMService
from backend.incident.diagnosis import diagnose
from backend.incident.fix_analyzer import analyze_known_bad_fixes
from backend.incident.stale_detector import detect_stale_fixes
from backend.incident.feedback import (
    attach_feedback_to_record,
    build_feedback_object,
    retain_feedback,
)
from backend.incident.closure import close_incident as _close_incident
from backend.incident.models import (
    ClosureRequest,
    ClosureResponse,
    DiagnoseRequest,
    DiagnoseResponse,
    FeedbackRequest,
    FeedbackResponse,
    FixAnalysisResult,
    IncidentRecord,
    IncidentStatus,
    StaleDetectionResult,
)
from backend.incident.normalizer import normalize_alert
from backend.incident.recall_planner import plan_recall
from backend.incident.resilience import NO_MEMORY_WARNING, is_hindsight_available
from backend.memory.hindsight import HindsightMemory

logger = logging.getLogger(__name__)


class IncidentResponseService:
    """
    Orchestrates the incident response pipeline (Slices 1 + 2).

    Injected at application startup via lifespan; shares the SAME
    HindsightMemory and LLMService instances used by the generic Agent.
    """

    def __init__(self, llm: LLMService, memory: HindsightMemory) -> None:
        self._llm    = llm
        self._memory = memory
        # Lightweight in-process store keyed by incident_id.
        # Replaced by a real DB in a later phase.
        self._store: dict[str, IncidentRecord] = {}

    # ── diagnose_alert (Slice 1 + Slice 2 F4/F5) ─────────────────────────────

    async def diagnose_alert(self, request: DiagnoseRequest) -> DiagnoseResponse:
        """
        Run the full pipeline for an incoming alert.

        Steps:
          1. F1  — normalize
          2. F13 — Hindsight health probe
          3. F2  — recall
          4. F3  — diagnose
          5. F4  — known-bad fix analysis
          6. F5  — stale-fix detection
          7.     — persist IncidentRecord
        """
        # Step 1 — F1 normalize (F14 applied inside normalizer)
        alert = normalize_alert(
            alert_text = request.alert_text,
            service    = request.service,
            logs       = request.logs,
            metrics    = request.metrics,
        )
        logger.info(
            "Alert normalized: service=%s sig=%s",
            alert.service, alert.error_signature,
        )

        # Step 2 — F13 health probe
        memory_available = await is_hindsight_available(self._memory)
        if not memory_available:
            logger.warning("Hindsight unavailable — entering no-memory mode.")

        # Step 3 — F2 recall
        bank_id = request.bank_id or "incidents"
        recall  = await plan_recall(alert, self._memory, bank_id)
        logger.info(
            "Recall complete: %d memories, used_memory=%s",
            len(recall.memories), recall.used_memory,
        )

        # Step 4 — F3 diagnose
        diagnosis = await diagnose(alert, recall, self._llm)

        if not memory_available and not diagnosis.memory_warning:
            diagnosis = diagnosis.model_copy(update={"memory_warning": NO_MEMORY_WARNING})

        # Step 5 — F4 known-bad fix analysis (deterministic, no LLM call)
        fix_analysis = analyze_known_bad_fixes(recall)
        logger.info(
            "F4: %d known-bad, %d mixed-results",
            len(fix_analysis.known_bad_fixes),
            len(fix_analysis.mixed_result_fixes),
        )

        # Step 6 — F5 stale-fix detection (deterministic)
        stale_detection = detect_stale_fixes(
            alert          = alert,
            recall         = recall,
            service_version = request.service_version,
            environment    = request.environment,
            deployment_id  = request.deployment_id,
        )
        logger.info("F5: %d stale assessments", len(stale_detection.assessments))

        # Step 7 — persist
        incident = IncidentRecord(
            incident_id     = diagnosis.incident_id,
            service         = alert.service,
            summary         = alert.summary,
            error_signature = alert.error_signature,
            severity        = alert.severity,
            started_at      = alert.started_at,
            status          = IncidentStatus.DIAGNOSED,
            logs            = request.logs,
            metrics         = request.metrics,
            alert           = alert,
            recall          = recall,
            diagnosis       = diagnosis,
            fix_analysis    = fix_analysis,
            stale_detection = stale_detection,
        )
        self._store[incident.incident_id] = incident
        logger.info("Incident %s persisted.", incident.incident_id)

        return DiagnoseResponse(
            incident_id     = incident.incident_id,
            alert           = alert,
            recall          = recall,
            diagnosis       = diagnosis,
            fix_analysis    = fix_analysis,
            stale_detection = stale_detection,
        )

    # ── add_feedback (F6) ─────────────────────────────────────────────────────

    async def add_feedback(
        self,
        incident_id: str,
        request: FeedbackRequest,
        bank_id: str = "incidents",
    ) -> FeedbackResponse:
        """
        Attach engineer feedback to an incident and retain it in Hindsight.

        Returns FeedbackResponse with acceptance status.
        Raises ValueError if the incident does not exist.
        """
        record = self._store.get(incident_id)
        if record is None:
            raise ValueError(f"Incident '{incident_id}' not found.")

        feedback = build_feedback_object(incident_id, request)
        updated  = attach_feedback_to_record(record, feedback)
        self._store[incident_id] = updated

        # Retain in Hindsight (non-fatal on failure)
        success, error = await retain_feedback(
            record  = updated,
            feedback = feedback,
            memory  = self._memory,
            bank_id = bank_id,
        )

        if not success:
            logger.warning("F6: Hindsight retain failed for feedback: %s", error)

        return FeedbackResponse(
            incident_id      = incident_id,
            feedback_accepted = True,
            message          = (
                f"Feedback recorded (type={request.feedback_type.value})."
                + ("" if success else " Warning: Hindsight retain failed — feedback stored locally only.")
            ),
        )

    # ── close_incident (F7) ───────────────────────────────────────────────────

    async def close_incident(
        self,
        incident_id: str,
        request: ClosureRequest,
        bank_id: str = "incidents",
    ) -> ClosureResponse:
        """
        Close an incident and write the resolution memory to Hindsight.

        Raises ValueError if incident not found.
        Always returns a ClosureResponse — Hindsight failures are reported
        in memory_writeback.succeeded=False.
        """
        record = self._store.get(incident_id)
        if record is None:
            raise ValueError(f"Incident '{incident_id}' not found.")

        if record.status == IncidentStatus.RESOLVED:
            # Idempotent — already closed, return current state
            from backend.incident.models import MemoryWritebackStatus
            return ClosureResponse(
                incident_id      = incident_id,
                status           = "already_closed",
                memory_writeback = MemoryWritebackStatus(attempted=False),
            )

        updated, response = await _close_incident(
            record  = record,
            closure = request,
            memory  = self._memory,
            bank_id = bank_id,
        )
        self._store[incident_id] = updated
        logger.info(
            "F7: Incident %s closed. write-back succeeded=%s",
            incident_id, response.memory_writeback.succeeded,
        )
        return response

    # ── Read helpers ──────────────────────────────────────────────────────────

    def get_incident(self, incident_id: str) -> IncidentRecord | None:
        return self._store.get(incident_id)

    def list_incidents(self) -> list[IncidentRecord]:
        return sorted(
            self._store.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )

    # ── Slice 3 & 4 Additions (F8–F13) ───────────────────────────────────────

    async def get_patterns(self, service: str | None = None, bank_id: str = "incidents") -> dict:
        """F8 — Pattern Digest using Hindsight REFLECT."""
        from backend.incident.patterns import get_pattern_digest
        return await get_pattern_digest(memory=self._memory, service=service, bank_id=bank_id)

    async def inspect_memories(self, bank_id: str = "incidents", service: str | None = None) -> dict:
        """F9 — Memory Inspector for real Hindsight memories."""
        from backend.incident.memory_inspector import inspect_memories
        return await inspect_memories(memory=self._memory, bank_id=bank_id, service=service)

    async def compare_control(self, request: DiagnoseRequest) -> dict:
        """F10 — Split-Screen Control Comparison (Baseline vs Hindsight Agent)."""
        from backend.incident.comparator import compare_control_vs_hindsight
        return await compare_control_vs_hindsight(request=request, service_instance=self)

    async def evaluate(self, bank_id: str = "incidents") -> dict:
        """F11 — Learning Scoreboard / Evaluation Harness."""
        from backend.incident.evaluator import run_evaluation
        return await run_evaluation(memory=self._memory, bank_id=bank_id)

    async def seed_data(self, bank_id: str = "incidents", count: int = 5) -> dict:
        """F12 — Data Seeding / Synthetic Incident Generator."""
        from backend.incident.generator import seed_incidents
        return await seed_incidents(memory=self._memory, bank_id=bank_id, count=count)

    async def get_resilience(self) -> dict:
        """F13 — Resilience and Health Probe Status."""
        from backend.incident.resilience import get_resilience_status
        return await get_resilience_status(memory=self._memory)

