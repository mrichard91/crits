import copy
from threading import local

from django.conf import settings

import crits.services

from crits.core.class_mapper import class_from_id
from crits.services.analysis_result import AnalysisConfig
from crits.services.core import AnalysisTask, ServiceConfigError
from crits.services.results import finish_task, insert_analysis_results, update_analysis_results
from crits.services.service import CRITsService


def _resolve_user(user):
    if hasattr(user, "username"):
        return user

    if user is None:
        return None

    from crits.core.user import CRITsUser

    return CRITsUser.objects(username=str(user)).first()


def execute_service_local(
    name,
    type_,
    id_,
    user,
    obj=None,
    custom_config=None,
    is_triage_run=False,
):
    """Execute a legacy service locally without importing Django handlers."""

    result = {"success": False, "analysis_id": "", "message": ""}
    custom_config = custom_config or {}

    if type_ not in settings.CRITS_TYPES:
        result["message"] = "Unknown CRITs type."
        return result

    resolved_user = _resolve_user(user)
    if not resolved_user:
        result["message"] = "Unable to find user."
        return result

    service = CRITsService.objects(name=name, enabled=True, status="available").first()
    if not service:
        result["message"] = "Service %s is unknown or not enabled." % name
        return result

    service_class = crits.services.manager.get_service_class(name)
    if not service_class:
        result["message"] = "Unable to get service class."
        return result

    if not obj:
        obj = class_from_id(type_, id_)
        if not obj:
            result["message"] = "Could not find object."
            return result

    if not service_class.supported_for_type(type_):
        result["message"] = "Service not supported for type '%s'" % type_
        return result

    local_obj = local()
    local_obj.obj = copy.deepcopy(obj)

    try:
        service_class.valid_for(local_obj.obj)
        if hasattr(local_obj.obj, "filedata") and local_obj.obj.filedata.grid_id:
            local_obj.obj.filedata.seek(0)
    except ServiceConfigError as e:
        result["message"] = str(e)
        return result

    db_config = service.config.to_dict() if service.config else {}
    try:
        service_class.validate_runtime(custom_config, db_config)
    except ServiceConfigError as e:
        result["message"] = str(e)
        return result

    final_config = dict(db_config)
    final_config.update(custom_config)

    form = service_class.bind_runtime_form(resolved_user.username, final_config)
    if form:
        if not form.is_valid():
            result["message"] = str(form.errors)
            return result

        final_config = dict(db_config)
        final_config.update(form.cleaned_data)

    service_instance = service_class(
        notify=update_analysis_results,
        complete=finish_task,
    )
    if is_triage_run:
        service_instance.is_triage_run = True

    saved_config = dict(final_config)
    service_class.save_runtime_config(saved_config)

    task = AnalysisTask(local_obj.obj, service_instance, resolved_user)
    task.config = AnalysisConfig(**saved_config)
    task.start()
    insert_analysis_results(task)

    service_instance.set_task(task)
    service_instance.execute(final_config)

    result["success"] = True
    result["analysis_id"] = task.task_id
    return result
