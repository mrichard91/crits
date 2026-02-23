"""Worker health check using Celery control.inspect."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def check_worker_health() -> dict[str, Any]:
    """Check Celery worker health via control.inspect.

    Returns a dict with:
        healthy: bool — True if at least one worker is responding
        workers: int — number of active workers
        details: dict — per-worker ping responses
        error: str | None — error message if health check failed
    """
    try:
        from crits_api.worker.app import celery_app

        inspector = celery_app.control.inspect(timeout=3.0)
        ping_responses = inspector.ping()

        if not ping_responses:
            return {
                "healthy": False,
                "workers": 0,
                "details": {},
                "error": "No workers responded to ping",
            }

        return {
            "healthy": True,
            "workers": len(ping_responses),
            "details": ping_responses,
            "error": None,
        }

    except Exception as e:
        logger.error("Worker health check failed: %s", e)
        return {
            "healthy": False,
            "workers": 0,
            "details": {},
            "error": str(e),
        }
