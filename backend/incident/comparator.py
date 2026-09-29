"""
backend/incident/comparator.py
-------------------------------
F10 — Split-Screen Control Comparison.

Compares Control / Baseline Agent (no historical memory) vs Hindsight-Enabled Agent
on the exact same incident alert.
"""

from __future__ import annotations

import logging
from backend.agent.llm import LLMService
from backend.incident.diagnosis import diagnose
from backend.incident.models import (
    DiagnoseRequest,
    DiagnoseResponse,
    RecallPlannerResult,
    FixAnalysisResult,
    StaleDetectionResult,
)
from backend.incident.normalizer import normalize_alert
from backend.memory.hindsight import HindsightMemory

logger = logging.getLogger(__name__)


async def compare_control_vs_hindsight(
    request: DiagnoseRequest,
    service_instance,  # IncidentResponseService
) -> dict:
    """
    Run side-by-side comparison on the same incoming alert.

    Returns:
        Dict with 'control' and 'hindsight' diagnosis responses.
    """
    # 1. Hindsight Agent run (full F1→F2→F3→F4→F5 pipeline)
    hindsight_resp: DiagnoseResponse = await service_instance.diagnose_alert(request)

    # 2. Control Agent run (F1→F3 pipeline with EMPTY recall memory)
    alert = normalize_alert(
        alert_text = request.alert_text,
        service    = request.service,
        logs       = request.logs,
        metrics    = request.metrics,
    )
    empty_recall = RecallPlannerResult(memories=[], queries=[], used_memory=False)

    # Control diagnosis without memory grounding
    control_diagnosis = await diagnose(alert, empty_recall, service_instance._llm)

    control_fix_analysis = FixAnalysisResult(
        known_bad_fixes=[],
        mixed_result_fixes=[],
        analysis_skipped=True,
    )
    control_stale_detection = StaleDetectionResult(
        assessments=[],
        analysis_skipped=True,
    )

    return {
        "alert": alert.model_dump(mode="json"),
        "control": {
            "mode": "baseline_no_memory",
            "used_memory": False,
            "recalled_memories_count": 0,
            "diagnosis": control_diagnosis.model_dump(mode="json"),
            "fix_analysis": control_fix_analysis.model_dump(mode="json"),
            "stale_detection": control_stale_detection.model_dump(mode="json"),
        },
        "hindsight": {
            "mode": "hindsight_enabled",
            "used_memory": hindsight_resp.recall.used_memory,
            "recalled_memories_count": len(hindsight_resp.recall.memories),
            "diagnosis": hindsight_resp.diagnosis.model_dump(mode="json"),
            "fix_analysis": hindsight_resp.fix_analysis.model_dump(mode="json"),
            "stale_detection": hindsight_resp.stale_detection.model_dump(mode="json"),
        },
    }
