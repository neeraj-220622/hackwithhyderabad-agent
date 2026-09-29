"""
backend/incident/generator.py
------------------------------
F12 — Data Seeding / Synthetic Incident Generator.

Seeds realistic synthetic historical incident records into Hindsight
to allow instant demonstration of recall (F2), known-bad fix detection (F4),
outdated-fix detection (F5), and pattern digests (F8).
"""

from __future__ import annotations

import logging
from backend.incident.redaction import redact
from backend.memory.hindsight import HindsightMemory, HindsightMemoryError

logger = logging.getLogger(__name__)

SYNTHETIC_INCIDENTS = [
    {
        "service": "payments-api",
        "error_signature": "DB_POOL_EXHAUSTED",
        "summary": "payments-api connection pool exhausted — 10/10 active connections",
        "version": "3.4",
        "env": "production",
        "memory_text": (
            "[INCIDENT RESOLUTION]\n"
            "Service       : payments-api\n"
            "Incident ID   : inc-synth-001\n"
            "Error Sig     : DB_POOL_EXHAUSTED\n"
            "Summary       : payments-api connection pool exhausted — all connections timing out\n"
            "Outcome       : resolved\n\n"
            "Confirmed Root Cause: High query spike exhausted max connections (10).\n"
            "Resolution Action: Increased POOL_SIZE from 10 to 50 in payments-api config.\n"
            "Success: True\n\n"
            "Failed Fixes (Do Not Repeat):\n"
            "  - Restart all pods: Restart failed to resolve issue — connection pool remained full.\n\n"
            "Engineer Feedback:\n"
            "  [corrected] by eng-001: Restart runbook failed. Increase POOL_SIZE after verifying DB limits."
        ),
    },
    {
        "service": "payments-api",
        "error_signature": "VERSION_2_1_POOL_LIMIT",
        "summary": "payments-api v2.1 connection pool limit tuning",
        "version": "2.1",
        "env": "production",
        "memory_text": (
            "[INCIDENT RESOLUTION]\n"
            "Service       : payments-api\n"
            "Incident ID   : inc-synth-002\n"
            "Error Sig     : VERSION_2_1_POOL_LIMIT\n"
            "Summary       : payments-api version 2.1 pool limit tuning\n"
            "Outcome       : resolved\n\n"
            "Confirmed Root Cause: v2.1 connection pool default size was 10.\n"
            "Resolution Action: Increased POOL_SIZE from 10 to 50. Succeeded in environment production."
        ),
    },
    {
        "service": "auth-service",
        "error_signature": "OOM_KILLED_CONTAINER",
        "summary": "auth-service container OOMKilled",
        "version": "1.2",
        "env": "production",
        "memory_text": (
            "[INCIDENT RESOLUTION]\n"
            "Service       : auth-service\n"
            "Incident ID   : inc-synth-003\n"
            "Error Sig     : OOM_KILLED_CONTAINER\n"
            "Summary       : auth-service container killed due to memory limit breach\n"
            "Outcome       : resolved\n\n"
            "Confirmed Root Cause: Token verification cache memory leak.\n"
            "Resolution Action: Fixed memory leak in JWT cache and increased pod memory limit from 512Mi to 1Gi.\n"
            "Success: True\n\n"
            "Failed Fixes (Do Not Repeat):\n"
            "  - Pod restart: Restarting pod failed — memory filled up again within 5 minutes."
        ),
    },
    {
        "service": "orders-service",
        "error_signature": "QUERY_TIMEOUT_CHECKOUT",
        "summary": "orders-service DB timeout on checkout endpoint",
        "version": "4.0",
        "env": "production",
        "memory_text": (
            "[INCIDENT RESOLUTION]\n"
            "Service       : orders-service\n"
            "Incident ID   : inc-synth-004\n"
            "Error Sig     : QUERY_TIMEOUT_CHECKOUT\n"
            "Summary       : orders-service database query timeout during checkout\n"
            "Outcome       : resolved\n\n"
            "Confirmed Root Cause: Unindexed query on orders.customer_id under heavy load.\n"
            "Resolution Action: Created index idx_orders_customer_id on checkout DB.\n"
            "Success: True"
        ),
    },
    {
        "service": "notification-service",
        "error_signature": "KAFKA_BROKER_REFUSED",
        "summary": "notification-service Kafka connection refused",
        "version": "2.0",
        "env": "production",
        "memory_text": (
            "[INCIDENT RESOLUTION]\n"
            "Service       : notification-service\n"
            "Incident ID   : inc-synth-005\n"
            "Error Sig     : KAFKA_BROKER_REFUSED\n"
            "Summary       : notification-service failing to push email events to Kafka\n"
            "Outcome       : resolved\n\n"
            "Confirmed Root Cause: Stale KAFKA_BROKERS IP address in environment config.\n"
            "Resolution Action: Updated KAFKA_BROKERS URL in Kubernetes secret and restarted service.\n"
            "Success: True"
        ),
    },
]


async def seed_incidents(
    memory: HindsightMemory,
    bank_id: str = "incidents",
    count: int = 5,
) -> dict:
    """
    Seed synthetic historical incident records into Hindsight.

    Returns:
        Dict with created, retained, failed counts.
    """
    try:
        await memory.ensure_bank(bank_id)
    except Exception as exc:
        logger.warning("Could not ensure bank '%s' for seeding: %s", bank_id, exc)

    items_to_seed = SYNTHETIC_INCIDENTS[:count]
    retained = 0
    failed = 0
    errors = []

    for item in items_to_seed:
        # Apply F14 redaction
        clean_text = redact(item["memory_text"])
        try:
            await memory.remember(
                bank_id = bank_id,
                content = clean_text,
                context = "incident resolution",
            )
            retained += 1
        except (HindsightMemoryError, Exception) as exc:
            failed += 1
            err_str = str(exc)
            logger.warning("Seeding failed for %s: %s", item["service"], err_str)
            errors.append(f"{item['service']}: {err_str[:80]}")

    return {
        "created": len(items_to_seed),
        "retained": retained,
        "failed": failed,
        "bank_id": bank_id,
        "errors": errors if errors else None,
        "status": "ok" if failed == 0 else ("partial" if retained > 0 else "degraded"),
    }
