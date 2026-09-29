"""
backend/api/incident_routes.py
-------------------------------
FastAPI routes for the Incident Response module (Part 9).

Slice 1 endpoints:
  POST /api/alerts/diagnose      — run F1→F2→F3 pipeline

Slice 2 will add:
  POST /api/incidents/{id}/feedback
  POST /api/incidents/{id}/close

Slice 3 will add:
  GET  /api/incidents/{id}
  GET  /api/incidents/{id}/memory
  GET  /api/patterns/{service}
  POST /api/evaluate
  POST /api/control/compare
  POST /api/seed

IMPORTANT: Does NOT break or modify:
  POST /api/agent/chat
  GET  /api/agent/memory/{user_id}
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from backend.incident.models import DiagnoseRequest, DiagnoseResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# ── POST /api/alerts/diagnose ─────────────────────────────────────────────────

@router.post(
    "/diagnose",
    response_model = DiagnoseResponse,
    summary        = "Diagnose an operational alert",
    description    = (
        "Accepts a free-text alert (plus optional service name, logs, metrics) "
        "and runs the full F1→F14→F2→F3 incident response pipeline. "
        "Returns a structured diagnosis grounded in recalled Hindsight memories."
    ),
)
async def diagnose_alert(request: Request, body: DiagnoseRequest) -> DiagnoseResponse:
    """
    POST /api/alerts/diagnose

    Run the Slice 1 incident pipeline:
      F1  — normalize alert
      F14 — redact (applied inside normalizer)
      F2  — recall memories from Hindsight
      F3  — produce evidence-cited diagnosis
    """
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        raise HTTPException(
            status_code = 503,
            detail      = (
                "Incident Response service is not available. "
                "Check LLM and Hindsight configuration."
            ),
        )

    try:
        return await incident_svc.diagnose_alert(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error in diagnose_alert: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.") from exc


# ── GET /api/alerts/incidents (list) ─────────────────────────────────────────

@router.get(
    "/incidents",
    summary     = "List all diagnosed incidents",
    description = "Returns all incidents processed in this session (lightweight in-memory store).",
)
async def list_incidents(request: Request) -> dict:
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        raise HTTPException(status_code=503, detail="Incident Response service not available.")

    records = incident_svc.list_incidents()
    return {
        "total": len(records),
        "incidents": [
            {
                "incident_id":     r.incident_id,
                "service":         r.service,
                "summary":         r.summary,
                "error_signature": r.error_signature,
                "severity":        r.severity,
                "status":          r.status,
                "created_at":      r.created_at.isoformat(),
            }
            for r in records
        ],
    }


# ── GET /api/alerts/incidents/{incident_id} ───────────────────────────────────

@router.get(
    "/incidents/{incident_id}",
    summary     = "Get a single incident by ID",
)
async def get_incident(request: Request, incident_id: str) -> dict:
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        raise HTTPException(status_code=503, detail="Incident Response service not available.")

    record = incident_svc.get_incident(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    return record.model_dump(mode="json")


# ── POST /api/alerts/incidents/{incident_id}/feedback (F6) ───────────────────

from backend.incident.models import FeedbackRequest, FeedbackResponse  # noqa: E402

@router.post(
    "/incidents/{incident_id}/feedback",
    response_model = FeedbackResponse,
    summary        = "Submit engineer feedback on an incident (F6)",
    description    = (
        "Accepts structured engineer feedback (accepted/rejected/corrected) "
        "and retains it in Hindsight so future incidents can benefit."
    ),
)
async def submit_feedback(
    request: Request,
    incident_id: str,
    body: FeedbackRequest,
) -> FeedbackResponse:
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        raise HTTPException(status_code=503, detail="Incident Response service not available.")

    try:
        return await incident_svc.add_feedback(incident_id=incident_id, request=body)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error in submit_feedback: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.") from exc


# ── POST /api/alerts/incidents/{incident_id}/close (F7) ──────────────────────

from backend.incident.models import ClosureRequest, ClosureResponse  # noqa: E402

@router.post(
    "/incidents/{incident_id}/close",
    response_model = ClosureResponse,
    summary        = "Close an incident and write back to Hindsight (F7)",
    description    = (
        "Closes the incident, applies F14 redaction, and retains a structured "
        "learning memory in Hindsight for future recall."
    ),
)
async def close_incident(
    request: Request,
    incident_id: str,
    body: ClosureRequest,
) -> ClosureResponse:
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        raise HTTPException(status_code=503, detail="Incident Response service not available.")

    try:
        return await incident_svc.close_incident(incident_id=incident_id, request=body)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error in close_incident: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error.") from exc


# ── GET /api/alerts/patterns (F8) ─────────────────────────────────────────────

@router.get(
    "/patterns",
    summary     = "Get operational pattern digest from Hindsight (F8)",
    description = "Generates a pattern digest summarizing recurring errors, root causes, and failed fixes from Hindsight.",
)
async def get_patterns(
    request: Request,
    service: str | None = None,
    bank_id: str = "incidents",
) -> dict:
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        raise HTTPException(status_code=503, detail="Incident Response service not available.")
    return await incident_svc.get_patterns(service=service, bank_id=bank_id)


# ── GET /api/alerts/memories (F9) ─────────────────────────────────────────────

@router.get(
    "/memories",
    summary     = "Inspect real Hindsight incident memories (F9)",
    description = "Retrieves raw structured incident learning memories stored in Hindsight.",
)
async def inspect_memories(
    request: Request,
    bank_id: str = "incidents",
    service: str | None = None,
) -> dict:
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        raise HTTPException(status_code=503, detail="Incident Response service not available.")
    return await incident_svc.inspect_memories(bank_id=bank_id, service=service)


# ── POST /api/alerts/compare (F10) ────────────────────────────────────────────

@router.post(
    "/compare",
    summary     = "Run Control vs Hindsight split-screen comparison (F10)",
    description = "Diagnoses the same alert twice: once with Control (no memory) and once with Hindsight memory.",
)
async def compare_control(request: Request, body: DiagnoseRequest) -> dict:
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        raise HTTPException(status_code=503, detail="Incident Response service not available.")
    return await incident_svc.compare_control(body)


# ── POST /api/alerts/evaluate (F11) ───────────────────────────────────────────

@router.post(
    "/evaluate",
    summary     = "Run learning evaluation benchmark (F11)",
    description = "Executes evaluation harness comparing Baseline vs Hindsight across benchmark scenarios.",
)
async def evaluate(request: Request, bank_id: str = "incidents") -> dict:
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        raise HTTPException(status_code=503, detail="Incident Response service not available.")
    return await incident_svc.evaluate(bank_id=bank_id)


# ── POST /api/alerts/seed (F12) ───────────────────────────────────────────────

@router.post(
    "/seed",
    summary     = "Seed synthetic incident memories into Hindsight (F12)",
    description = "Populates Hindsight bank with realistic synthetic historical incidents.",
)
async def seed_data(
    request: Request,
    bank_id: str = "incidents",
    count: int = 5,
) -> dict:
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        raise HTTPException(status_code=503, detail="Incident Response service not available.")
    return await incident_svc.seed_data(bank_id=bank_id, count=count)


# ── GET /api/alerts/resilience (F13) ──────────────────────────────────────────

@router.get(
    "/resilience",
    summary     = "Get Hindsight health probe & resilience status (F13)",
)
async def get_resilience(request: Request) -> dict:
    incident_svc = getattr(request.app.state, "incident_svc", None)
    if not incident_svc:
        return {"hindsight_connected": False, "status": "degraded", "warning": "Service unavailable."}
    return await incident_svc.get_resilience()

