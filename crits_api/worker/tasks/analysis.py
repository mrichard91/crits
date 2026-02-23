"""Celery tasks for service execution.

run_service_task — runs a single service on a TLO
run_triage_task — fans out all triage services via celery.group()
"""

import logging
from typing import Any

from celery import group

from crits_api.worker.app import celery_app
from crits_api.worker.tasks.base import CRITsTask

logger = logging.getLogger(__name__)


@celery_app.task(base=CRITsTask, bind=True, name="crits_api.worker.tasks.analysis.run_service_task")
def run_service_task(
    self: CRITsTask,
    service_name: str,
    obj_type: str,
    obj_id: str,
    username: str,
    custom_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a single analysis service on a TLO.

    Called via: run_service_task.delay(service_name, obj_type, obj_id, username, config)
    """
    from crits_api.worker.services.execution import execute_service

    logger.info(
        "Running service '%s' on %s/%s for user '%s'", service_name, obj_type, obj_id, username
    )

    try:
        return execute_service(
            service_name=service_name,
            obj_type=obj_type,
            obj_id=obj_id,
            username=username,
            custom_config=custom_config,
        )
    except Exception as exc:
        logger.exception("Service task '%s' failed", service_name)
        raise self.retry(exc=exc) from exc


@celery_app.task(base=CRITsTask, bind=True, name="crits_api.worker.tasks.analysis.run_triage_task")
def run_triage_task(
    self: CRITsTask,
    obj_type: str,
    obj_id: str,
    username: str,
) -> dict[str, Any]:
    """Run all triage services on a TLO via fan-out.

    Each triage service runs as an independent retriable task using celery.group().
    """
    from crits_api.worker.services.registry import (
        ensure_services_registered,
        get_triage_service_names,
    )

    ensure_services_registered()
    triage_names = get_triage_service_names()

    if not triage_names:
        logger.info("No triage services configured for %s/%s", obj_type, obj_id)
        return {"success": True, "message": "No triage services configured", "dispatched": 0}

    logger.info(
        "Dispatching triage for %s/%s: %s",
        obj_type,
        obj_id,
        ", ".join(triage_names),
    )

    # Fan out each service as an independent task
    job = group(run_service_task.s(name, obj_type, obj_id, username) for name in triage_names)
    job.apply_async()

    return {
        "success": True,
        "message": f"Dispatched {len(triage_names)} triage services",
        "dispatched": len(triage_names),
        "services": triage_names,
    }
