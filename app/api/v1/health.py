"""
app/api/v1/health.py
────────────────────
Health check endpoints.

Two endpoints with distinct purposes:

  GET /health       → Liveness probe
    "Is the process alive?"
    Returns 200 immediately. No I/O. Used by load balancers and
    container orchestrators to detect crashed instances.

  GET /health/ready → Readiness probe
    "Is the app ready to serve traffic?"
    Checks external dependencies (DB, Redis, etc.).
    Returns 200 when ready, 503 when not.
    Used to delay traffic until the app is fully initialized.

Phase 1: readiness is always "ready" because we have no DB yet.
Phase 2+: readiness will check the DB connection, then Redis, etc.
"""

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health_check() -> dict:
    """
    Returns 200 if the application process is running.

    This endpoint must be:
      - Fast (no I/O)
      - Unauthenticated
      - Always 200 while the process is alive
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health/ready", summary="Readiness probe")
async def readiness_check() -> dict:
    """
    Returns 200 when the application is ready to serve requests.

    Phase 1: Always returns ready (no external dependencies yet).
    Later phases will check:
      - Database connectivity
      - Redis connectivity
      - Required environment variables
    """
    return {
        "status": "ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": {
            "database": "skipped (phase 1)",
            "redis": "skipped (phase 1)",
        },
    }
