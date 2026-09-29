"""
backend/incident/diagnosis.py
-----------------------------
F3 — Evidence-Cited Diagnosis.

CRITICAL RULE: Every evidence item shown to the user MUST correspond to an
actual recalled memory from F2. The LLM must NOT invent historical incidents.

Architecture:
  1. If recalled memories exist → build a memory-grounded prompt and call the LLM.
  2. Parse the LLM JSON response (retry up to 2× on parse failure — F13).
  3. For each hypothesis, the LLM is asked to cite memories by index.
     We then resolve those indices to actual RecalledMemory objects.
  4. If no relevant memories exist → return a clearly labelled generic diagnosis.
  5. Pydantic validation ensures the returned DiagnosisResult is always valid.

Never silently invent citations. If the LLM returns a citation index that
doesn't exist, it is silently dropped (not faked).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from backend.agent.llm import LLMService, LLMProviderError
from backend.incident.models import (
    DiagnosisResult,
    EvidenceItem,
    Hypothesis,
    NormalizedAlert,
    RecallPlannerResult,
    RecalledMemory,
)

logger = logging.getLogger(__name__)

MAX_RETRIES     = 2
MAX_MEMORIES_IN_PROMPT = 10   # limit context window usage


# ── Prompt construction ───────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert incident response AI.
Your job is to diagnose operational incidents based on the alert and any
relevant historical memories that have been recalled from the Hindsight
memory system.

CRITICAL RULES:
1. Every evidence item you cite MUST be a memory from the RECALLED MEMORIES
   section below, identified by its [N] index.
2. Do NOT invent historical incidents. If you have no relevant memory, say so.
3. Return ONLY valid JSON matching the schema below. No prose, no markdown.

OUTPUT SCHEMA (JSON):
{
  "hypotheses": [
    {
      "root_cause": "<string>",
      "confidence": <float 0-1>,
      "evidence_indices": [<int>, ...],
      "outdated_warning": ""
    }
  ],
  "recommended_steps": ["<string>", ...],
  "avoid": ["<string>", ...],
  "generic_diagnosis": <true|false>
}

If generic_diagnosis is true, hypotheses may have empty evidence_indices.
"""


def _build_user_prompt(alert: NormalizedAlert, recall: RecallPlannerResult) -> str:
    memories = recall.memories[:MAX_MEMORIES_IN_PROMPT]

    mem_block = ""
    if memories:
        items = []
        for i, m in enumerate(memories):
            label = f"[{i}] ({m.query_label})" if m.query_label else f"[{i}]"
            items.append(f"{label} {m.text}")
        mem_block = "\n".join(items)
    else:
        mem_block = "(No relevant memories found — produce a generic diagnosis.)"

    return f"""\
ALERT
-----
Service         : {alert.service}
Summary         : {alert.summary}
Error Signature : {alert.error_signature}
Severity        : {alert.severity}
Logs            :
{alert.logs_trimmed or "(none)"}

RECALLED MEMORIES (cite by index in evidence_indices)
-----------------------------------------------------
{mem_block}

Produce the JSON diagnosis now.
"""


# ── JSON extraction and validation ────────────────────────────────────────────

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json(text: str) -> dict[str, Any]:
    """
    Extract and parse JSON from LLM output.
    Handles both bare JSON and markdown code blocks.
    """
    # Try stripping markdown fences first
    m = _JSON_BLOCK_RE.search(text)
    if m:
        text = m.group(1)

    # Find first { ... } block
    start = text.find("{")
    end   = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM output.")
    return json.loads(text[start : end + 1])


def _resolve_evidence(
    indices: list[int],
    memories: list[RecalledMemory],
) -> list[EvidenceItem]:
    """
    Convert LLM-supplied memory indices into validated EvidenceItem objects.

    Indices that are out of range are silently dropped — we never fake evidence.
    """
    items: list[EvidenceItem] = []
    for idx in indices:
        if 0 <= idx < len(memories):
            m = memories[idx]
            items.append(
                EvidenceItem(
                    memory_text = m.text,
                    query_label = m.query_label,
                    memory_id   = m.memory_id,
                )
            )
        else:
            logger.warning("LLM cited out-of-range memory index %d — dropped.", idx)
    return items


def _parse_diagnosis(
    raw: dict[str, Any],
    memories: list[RecalledMemory],
    used_memory: bool,
) -> DiagnosisResult:
    """Build a validated DiagnosisResult from the raw LLM dict."""
    hypotheses: list[Hypothesis] = []
    for h in raw.get("hypotheses", []):
        evidence = _resolve_evidence(h.get("evidence_indices", []), memories)
        hypotheses.append(
            Hypothesis(
                root_cause       = str(h.get("root_cause", "Unknown")),
                confidence       = float(h.get("confidence", 0.5)),
                evidence         = evidence,
                outdated_warning = str(h.get("outdated_warning", "")),
            )
        )

    generic = bool(raw.get("generic_diagnosis", False))
    if not used_memory:
        generic = True

    return DiagnosisResult(
        hypotheses          = hypotheses,
        recommended_steps   = [str(s) for s in raw.get("recommended_steps", [])],
        avoid               = [str(s) for s in raw.get("avoid", [])],
        used_memory         = used_memory,
        generic_diagnosis   = generic,
        memory_warning      = "" if used_memory else (
            "No relevant historical memory found — this is a generic diagnosis."
        ),
    )


# ── Generic fallback (no LLM, no memory) ─────────────────────────────────────

def _generic_diagnosis(alert: NormalizedAlert) -> DiagnosisResult:
    """
    Return a clearly-labelled generic diagnosis when Hindsight has no
    relevant memories AND the LLM cannot provide a grounded response.
    """
    return DiagnosisResult(
        hypotheses=[
            Hypothesis(
                root_cause = (
                    f"Potential issue with {alert.service}: {alert.error_signature}"
                ),
                confidence = 0.3,
                evidence   = [],
            )
        ],
        recommended_steps=[
            "Check recent deployments and configuration changes.",
            "Review service logs for more context.",
            "Consult runbooks for this service.",
        ],
        avoid=[],
        used_memory       = False,
        generic_diagnosis = True,
        memory_warning    = (
            "No relevant historical memory found — this is a generic diagnosis "
            "and has NOT been grounded in previous incidents."
        ),
    )


# ── Public API ────────────────────────────────────────────────────────────────

async def diagnose(
    alert: NormalizedAlert,
    recall: RecallPlannerResult,
    llm: LLMService,
) -> DiagnosisResult:
    """
    Produce an evidence-cited diagnosis for the alert.

    Args:
        alert:  F1 normalized alert.
        recall: F2 recall planner result.
        llm:    The existing LLMService instance.

    Returns:
        DiagnosisResult — always valid, never raises.

    On failure (LLM error / malformed JSON after retries) falls back to
    _generic_diagnosis().
    """
    used_memory = recall.used_memory
    memories    = recall.memories

    # Build prompt
    user_prompt = _build_user_prompt(alert, recall)

    last_exc: Exception | None = None
    last_raw: str = ""

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw_text = await llm.generate(
                system_prompt = _SYSTEM_PROMPT,
                user_prompt   = user_prompt if attempt == 0 else (
                    user_prompt
                    + f"\n\nPREVIOUS ATTEMPT FAILED (JSON parse error): {last_exc}. "
                    "Return ONLY valid JSON."
                ),
            )
            last_raw = raw_text
            raw_dict = _extract_json(raw_text)
            return _parse_diagnosis(raw_dict, memories, used_memory)

        except LLMProviderError as exc:
            logger.error("LLM call failed on attempt %d: %s", attempt + 1, exc)
            last_exc = exc
            break   # LLM unavailable — don't retry

        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            logger.warning(
                "JSON parse failed on attempt %d: %s | raw=%s",
                attempt + 1, exc, last_raw[:200],
            )
            last_exc = exc
            # Retry loop continues

    # All retries exhausted or LLM unavailable → generic diagnosis
    logger.warning("Falling back to generic diagnosis after failures: %s", last_exc)
    return _generic_diagnosis(alert)
