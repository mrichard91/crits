import datetime
import logging

from crits.core.class_mapper import class_from_type
from crits.core.user_tools import user_sources
from crits.services.analysis_result import AnalysisResult, EmbeddedAnalysisResultLog

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

    date = str(datetime.datetime.now())
    ar = AnalysisResult.objects(analysis_id=analysis_id).first()
    if ar:
        AnalysisResult.objects(id=ar.id).update_one(
            set__status=status,
            set__finish_date=date,
        )

    results["success"] = True
    return results


def insert_analysis_results(task):
    """Insert a new analysis result document for a task."""

    ar = AnalysisResult()
    tdict = task.to_dict()
    tdict["analysis_id"] = tdict["id"]
    del tdict["id"]
    ar.merge(arg_dict=tdict)
    ar.save()


def update_analysis_results(task):
    """Persist the current state of an analysis task."""

    found = False
    ar = AnalysisResult.objects(analysis_id=task.task_id).first()
    if ar:
        found = True

    if not found:
        logger.warning("Tried to update a task that didn't exist.")
        insert_analysis_results(task)
        return

    tdict = task.to_dict()
    tdict["analysis_id"] = tdict["id"]
    del tdict["id"]

    new_dict = {}
    for key in tdict.keys():
        new_dict["set__%s" % key] = tdict[key]
    try:
        AnalysisResult.objects(id=ar.id).update_one(**new_dict)
    except Exception as e:
        task.status = "error"
        new_dict["set__results"] = []
        le = EmbeddedAnalysisResultLog()
        le.message = "DB Update Failed: %s" % e
        le.level = "error"
        le.datetime = str(datetime.datetime.now())
        new_dict["set__log"].append(le)
        try:
            AnalysisResult.objects(id=ar.id).update_one(**new_dict)
        except Exception:
            AnalysisResult.objects(id=ar.id).update_one(set__log=[le])
