import datetime
import logging

from crits.core.class_mapper import class_from_type
from crits.core.user_tools import user_sources
from crits.services.analysis_records import (
    create_analysis_record_from_task,
    finish_analysis_record,
    get_analysis_record,
    update_analysis_record_from_task,
)

logger = logging.getLogger(__name__)


def _resolve_user(user):
    """Return a CRITsUser when given either a user object or username string."""

    if hasattr(user, "username"):
        return user

    if user is None:
        return None

    from crits.core.user import CRITsUser

    return CRITsUser.objects(username=str(user)).first()


def finish_task(object_type, object_id, analysis_id, status, user):
    """Mark an analysis task finished."""

    results = {"success": False}
    if not status:
        status = "completed"
    if status not in ("error", "completed"):
        status = "completed"
    if not object_type or not object_id or not analysis_id:
        results["message"] = "Must supply object id/type and analysis id."
        return results

    klass = class_from_type(object_type)
    params = {"id": object_id}

    resolved_user = _resolve_user(user)
    if resolved_user and hasattr(klass, "source"):
        params["source__name__in"] = user_sources(resolved_user)

    obj = klass.objects(**params).first()
    if not obj:
        results["message"] = "Could not find object to add results to."
        return results

    analysis_record = get_analysis_record(analysis_id)
    if analysis_record:
        finish_analysis_record(
            analysis_id=analysis_id,
            status=status,
        )

    results["success"] = True
    return results


def insert_analysis_results(task):
    """Insert a new analysis result document for a task."""

    create_analysis_record_from_task(task)


def update_analysis_results(task):
    """Persist the current state of an analysis task."""

    if not get_analysis_record(task.task_id):
        logger.warning("Tried to update a task that didn't exist.")
        insert_analysis_results(task)
        return
    try:
        update_analysis_record_from_task(task)
    except Exception as e:
        task.status = "error"
        task.results = []
        task.log.append(
            {
                "message": "DB Update Failed: %s" % e,
                "level": "error",
                "datetime": str(datetime.datetime.now()),
            }
        )
        try:
            update_analysis_record_from_task(task)
        except Exception:
            logger.exception("Failed to persist analysis error log for %s", task.task_id)
