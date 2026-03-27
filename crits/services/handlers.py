import ast
import csv
import datetime
import html
import io
import json
import logging
import copy
import re

from django.http import HttpResponse
from multiprocessing import Process
from threading import Thread, local

from multiprocessing.pool import Pool, ThreadPool

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render

import crits.services

from crits.core.class_mapper import class_from_type, class_from_id
from crits.core.crits_mongoengine import json_handler
from crits.core.handlers import build_jtable
from crits.services.analysis_records import (
    append_analysis_log,
    append_analysis_results,
    count_analysis_records,
    delete_analysis_record_by_id,
    find_analysis_records,
)
from crits.services.core import ServiceConfigError, AnalysisTask
from crits.services.results import finish_task, insert_analysis_results, update_analysis_results
from crits.services.service_records import (
    find_service_records,
    get_service_record,
    update_service_record,
)

logger = logging.getLogger(__name__)

ANALYSIS_RESULT_JTABLE_OPTS = {
    'details_url': 'crits-services-views-analysis_result',
    'details_url_key': 'id',
    'default_sort': "start_date DESC",
    'searchurl': 'crits-services-views-analysis_results_listing',
    'fields': ["object_type", "service_name", "version", "start_date", "finish_date",
               "results", "object_id", "id"],
    'jtopts_fields': ["details", "object_type", "service_name", "version", "start_date",
                      "finish_date", "results", "id"],
    'hidden_fields': ["object_id", "id"],
    'linked_fields': ["object_type", "service_name"],
    'details_link': 'details',
    'no_sort': ['details'],
}


def _analysis_results_query(request):
    params = request.GET.copy()
    params.update(request.POST.copy())

    query: dict[str, object] = {}

    for key in ("analysis_id", "object_type", "object_id", "service_name", "version", "status"):
        value = params.get(key)
        if value:
            query[key] = value

    if params.get("otype") and "object_type" not in query:
        query["object_type"] = params.get("otype")

    analysis_result_value = params.get("analysis_result")
    if analysis_result_value:
        query["results.result"] = analysis_result_value

    term = params.get("q", "")
    if term:
        pattern = re.escape(term)
        search_type = params.get("search_type", "")
        if search_type == "analysis_result":
            query["results.result"] = {"$regex": pattern, "$options": "i"}
        else:
            query["$or"] = [
                {"service_name": {"$regex": pattern, "$options": "i"}},
                {"object_type": {"$regex": pattern, "$options": "i"}},
                {"object_id": {"$regex": pattern, "$options": "i"}},
                {"analyst": {"$regex": pattern, "$options": "i"}},
                {"results.result": {"$regex": pattern, "$options": "i"}},
                {"version": {"$regex": pattern, "$options": "i"}},
            ]

    return query


def _analysis_results_sort(request):
    sort_expr = request.GET.get("jtSorting", ANALYSIS_RESULT_JTABLE_OPTS["default_sort"])
    allowed_fields = {
        "object_type",
        "service_name",
        "version",
        "start_date",
        "finish_date",
        "object_id",
        "status",
        "analyst",
        "analysis_id",
    }
    sort_spec: list[tuple[str, int]] = []

    for key in sort_expr.split(","):
        parts = key.split()
        if len(parts) != 2:
            continue
        keyname, keyorder = parts
        if keyname not in allowed_fields:
            continue
        direction = -1 if keyorder.upper() == "DESC" else 1
        sort_spec.append((keyname, direction))

    return sort_spec or [("start_date", -1)]


def _analysis_result_record(record):
    return {
        "object_type": html.escape(record.object_type),
        "service_name": html.escape(record.service_name),
        "version": html.escape(record.version),
        "start_date": html.escape(record.start_date),
        "finish_date": html.escape(record.finish_date),
        "results": len(record.results),
        "object_id": html.escape(record.object_id),
        "id": record.id,
        "url": reverse('crits-services-views-analysis_result', args=(record.id,)),
    }

def generate_analysis_results_csv(request):
    """
    Generate a CSV file of the Analysis Results information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    query = _analysis_results_query(request)
    requested_fields = request.GET.get("fields", "")
    fields = [field for field in requested_fields.split(",") if field] or [
        "object_type",
        "service_name",
        "version",
        "start_date",
        "finish_date",
        "results",
        "object_id",
    ]

    records = find_analysis_records(
        query,
        limit=max(count_analysis_records(query), 1),
        sort=_analysis_results_sort(request),
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(fields)

    for record in records:
        formatted = _analysis_result_record(record)
        writer.writerow([formatted.get(field, "") for field in fields])

    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response['Content-Disposition'] = "attachment;filename=crits-AnalysisResult-export.csv"
    return response

def generate_analysis_results_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    type_ = "analysis_result"
    mapper = ANALYSIS_RESULT_JTABLE_OPTS
    if option == "jtlist":
        page_size = request.user.get_preference('ui', 'table_page_size', 25)
        skip = int(request.GET.get("jtStartIndex", "0"))
        if "jtLimit" in request.GET:
            page_size = int(request.GET['jtLimit'])
        else:
            page_size = int(request.GET.get("jtPageSize", page_size))

        query = _analysis_results_query(request)
        response = {
            "Result": "OK",
            "Records": [
                _analysis_result_record(record)
                for record in find_analysis_records(
                    query,
                    limit=page_size,
                    offset=skip,
                    sort=_analysis_results_sort(request),
                )
            ],
            "TotalRecordCount": count_analysis_records(query),
        }
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    if option == "jtdelete":
        response = {"Result": "ERROR"}
        if "id" in request.POST and delete_analysis_record_by_id(request.POST["id"]):
            response = {"Result": "OK"}
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Analysis Results",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits-services-views-%ss_listing' % type_,
                           args=('jtlist',)),
        'deleteurl': reverse('crits-services-views-%ss_listing' % type_,
                             args=('jtdelete',)),
        'searchurl': reverse(mapper['searchurl']),
        'fields': mapper['jtopts_fields'],
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link'],
        'no_sort': mapper['no_sort']
    }
    jtable = build_jtable(jtopts,request)
    jtable['toolbar'] = [
    ]
    if option == "inline":
        return render(request, "jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button' : '%ss_tab' % type_},
                                  )
    else:
        return render(request, "%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  )

def service_work_handler(service_instance, final_config):
    """
    Handles a unit of work for a service by calling the service's "execute"
    method. This function is generally called by processes/threads. Also
    this function is needed because it is picklable and passing in the
    service_instance.execute method is not picklable because it is an
    instance method.

    :param service_instance: The service instance that the work will be performed in
    :type service_instance: crits.services.core.Service
    :param service_instance: The service's configuration settings
    :type service_instance: dict
    """

    service_instance.execute(final_config)


def run_service(name, type_, id_, user, obj=None, execute='local',
                custom_config={}, is_triage_run=False, **kwargs):
    """
    Run a service.

    :param name: The name of the service to run.
    :type name: str
    :param type_: The type of the object.
    :type type_: str
    :param id_: The identifier of the object.
    :type id_: str
    :param user: The user running the service.
    :type user: str
    :param obj: The CRITs object, if given this overrides crits_type and identifier.
    :type obj: CRITs object.
    :param user: The user updating the results.
    :type user: :class:`crits.core.user.CRITsUser`
    :param execute: The execution type.
    :type execute: str
    :param custom_config: Use a custom configuration for this run.
    :type custom_config: dict
    """

    result = {'success': False}
    if type_ not in settings.CRITS_TYPES:
        result['html'] = "Unknown CRITs type."
        return result

    if name not in enabled_services():
        result['html'] = "Service %s is unknown or not enabled." % name
        return result

    service_class = crits.services.manager.get_service_class(name)
    if not service_class:
        result['html'] = "Unable to get service class."
        return result

    if not obj:
        obj = class_from_id(type_, id_)
        if not obj:
            result['html'] = 'Could not find object.'
            return result

    service = get_service_record(name)
    if not service:
        result['html'] = "Unable to find service in database."
        return result

    # See if the object is a supported type for the service.
    if not service_class.supported_for_type(type_):
        result['html'] = "Service not supported for type '%s'" % type_
        return result

    # When running in threaded mode, each thread needs to have its own copy of
    # the object. If we do not do this then one thread may read() from the
    # object (to get the binary) and then the second would would read() without
    # knowing and get undefined behavior as the file pointer would be who knows
    # where. By giving each thread a local copy they can operate independently.
    #
    # When not running in thread mode this has no effect except wasted memory.
    local_obj = local()
    local_obj.obj = copy.deepcopy(obj)

    # Give the service a chance to check for required fields.
    try:
        service_class.valid_for(local_obj.obj)
        if hasattr(local_obj.obj, 'filedata'):
            if local_obj.obj.filedata.grid_id:
                # Reset back to the start so the service gets the full file.
                local_obj.obj.filedata.seek(0)
    except ServiceConfigError as e:
        result['html'] = str(e)
        return result

    # Get the config from the database and validate the submitted options
    # exist.
    db_config = dict(service.config)
    try:
        service_class.validate_runtime(custom_config, db_config)
    except ServiceConfigError as e:
        result['html'] = str(e)
        return result

    final_config = db_config
    # Merge the submitted config with the one from the database.
    # This is because not all config options may be submitted.
    final_config.update(custom_config)

    form = service_class.bind_runtime_form(user.username, final_config)
    if form:
        if not form.is_valid():
            # TODO: return corrected form via AJAX
            result['html'] = str(form.errors)
            return result

        # If the form is valid, create the config using the cleaned data.
        final_config = db_config
        final_config.update(form.cleaned_data)

    logger.info("Running %s on %s, execute=%s" % (name, local_obj.obj.id, execute))
    service_instance = service_class(notify=update_analysis_results,
                                     complete=finish_task)
    # Determine if this service is being run via triage
    if is_triage_run:
        service_instance.is_triage_run = True

    # Give the service a chance to modify the config that gets saved to the DB.
    saved_config = dict(final_config)
    service_class.save_runtime_config(saved_config)

    task = AnalysisTask(local_obj.obj, service_instance, user)
    task.config = dict(saved_config)
    task.start()
    add_task(task)

    service_instance.set_task(task)

    if execute == 'process':
        p = Process(target=service_instance.execute, args=(final_config,))
        p.start()
    elif execute == 'thread':
        t = Thread(target=service_instance.execute, args=(final_config,))
        t.start()
    elif execute == 'process_pool':
        if __service_process_pool__ is not None and service.compatability_mode != True:
            __service_process_pool__.apply_async(func=service_work_handler,
                                                 args=(service_instance, final_config,))
        else:
            logger.warning("Could not run %s on %s, execute=%s, running in process mode" % (name, local_obj.obj.id, execute))
            p = Process(target=service_instance.execute, args=(final_config,))
            p.start()
    elif execute == 'thread_pool':
        if __service_thread_pool__ is not None and service.compatability_mode != True:
            __service_thread_pool__.apply_async(func=service_work_handler,
                                                args=(service_instance, final_config,))
        else:
            logger.warning("Could not run %s on %s, execute=%s, running in thread mode" % (name, local_obj.obj.id, execute))
            t = Thread(target=service_instance.execute, args=(final_config,))
            t.start()
    elif execute == 'local':
        service_instance.execute(final_config)

    # Return after starting thread so web request can complete.
    result['success'] = True
    return result

def add_task(task):
    """
    Add a new task.
    """

    logger.debug("Adding task %s" % task)
    insert_analysis_results(task)

def run_triage(obj, user):
    """
    Run all services marked as triage against this top-level object.

    :param obj: The CRITs top-level object class.
    :type obj: Class which inherits from
               :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
    :param user: The user requesting the services to be run.
    :type user: :class:`crits.core.user.CRITsUser`
    """

    services = triage_services()
    for service_name in services:
        try:
            run_service(service_name,
                        obj._meta['crits_type'],
                        obj.id,
                        user,
                        obj=obj,
                        execute=settings.SERVICE_MODEL,
                        custom_config={},
                        is_triage_run=True)
        except:
            pass
    return


def add_result(object_type, object_id, analysis_id, result, type_, subtype,
               user):
    """
    add_results wrapper for a single result.

    :param object_type: The top-level object type.
    :type object_type: str
    :param object_id: The ObjectId to search for.
    :type object_id: str
    :param analysis_id: The ID of the task to update.
    :type analysis_id: str
    :param result: The result to append.
    :type result: str
    :param type_: The result type.
    :type type_: str
    :param subtype: The result subtype.
    :type subtype: str
    :param user: The user updating the results.
    :type user: :class:`crits.core.user.CRITsUser`
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    return add_results(object_type, object_id, analysis_id, [result], [type_],
                      [subtype], user)


def add_results(object_type, object_id, analysis_id, result, type_, subtype,
                user):
    """
    Add multiple results to an analysis task.

    :param object_type: The top-level object type.
    :type object_type: str
    :param object_id: The ObjectId to search for.
    :type object_id: str
    :param analysis_id: The ID of the task to update.
    :type analysis_id: str
    :param result: The list of result to append.
    :type result: list of str
    :param type_: The list of result types.
    :type type_: list of str
    :param subtype: The list of result subtypes.
    :type subtype: list of str
    :param user: The user updating the results.
    :type user: :class:`crits.core.user.CRITsUser`
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    res = {'success': False}
    if not object_type or not object_id or not analysis_id:
        res['message'] = "Must supply object id/type and analysis id."
        return res

    # Validate user can add service results to this TLO.
    klass = class_from_type(object_type)
    sources = user.get_sources_list()
    obj = klass.objects(id=object_id, source__name__in=sources).first()
    if not obj:
        res['message'] = "Could not find object to add results to."
        return res

    if not(result and type_ and subtype):
        res['message'] = "Need a result, type, and subtype to add a result."
        return res

    if not(len(result) == len(type_) == len(subtype)):
        res['message'] = "result, type, and subtype need to be the same length."
        return res

    # Update analysis results
    final_list = []
    for key, r in enumerate(result):
        final = {}
        final['subtype'] = subtype[key]
        final['result'] = r
        tmp = ast.literal_eval(type_[key])
        for k in tmp:
            final[k] = tmp[k]
        final_list.append(final)

    if append_analysis_results(analysis_id, final_list):
        res['success'] = True
    else:
        res['message'] = "Could not find task to add results to."
    return res


def add_log(object_type, object_id, analysis_id, log_message, level, user):
    """
    Add a log entry to an analysis task.

    :param object_type: The top-level object type.
    :type object_type: str
    :param object_id: The ObjectId to search for.
    :type object_id: str
    :param analysis_id: The ID of the task to update.
    :type analysis_id: str
    :param log_message: The log entry to append.
    :type log_message: dict
    :param level: The log level.
    :type level: str
    :param user: The user updating the log.
    :type user: :class:`crits.core.user.CRITsUser`
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    results = {'success': False}
    if not object_type or not object_id or not analysis_id:
        results['message'] = "Must supply object id/type and analysis id."
        return results

    # Validate user can add service results to this TLO.
    klass = class_from_type(object_type)
    sources = user.get_sources_list()
    obj = klass.objects(id=object_id, source__name__in=sources).first()
    if not obj:
        results['message'] = "Could not find object to add results to."
        return results

    if append_analysis_log(analysis_id, log_message, level):
        results['success'] = True
    else:
        results['message'] = "Could not find task to add log to."
    return results



def update_config(service_name, config, user):
    """
    Update the configuration for a service.
    """
    service = get_service_record(service_name)
    if not service:
        return {'success': False, 'message': 'Unknown service.'}

    update_service_record(service_name, {"config": dict(config)})
    return {'success': True}

def get_service_config(name):
    status = {'success': False}
    services = find_service_records({"name": name, "status": {"$ne": "unavailable"}})
    service = services[0] if services else None
    if not service:
        status['error'] = 'Service "%s" is unavailable. Please review error logs.' % name
        return status

    config = dict(service.config)
    service_class = crits.services.manager.get_service_class(name)
    if not service_class:
        status['error'] = 'Service "%s" is unavilable. Please review error logs.' % name
        return status
    display_config = service_class.get_config_details(config)

    status['config'] = display_config
    status['config_error'] = _get_config_error(service)
    status['service'] = service

    status['success'] = True
    return status


def _get_config_error(service):
    """
    Return a string describing the error in the service configuration.

    Returns None if there are no errors.
    """

    error = None
    name = service.name
    config = dict(service.config)
    if service.status == 'misconfigured':
        service_class = crits.services.manager.get_service_class(name)
        try:
            service_class.parse_config(config)
        except Exception as e:
            error = str(e)
    return error


def do_edit_config(name, user, post_data=None):
    status = {'success': False}
    services = find_service_records({"name": name, "status": {"$ne": "unavailable"}})
    service = services[0] if services else None
    if not service:
        status['config_error'] = 'Service "%s" is unavailable. Please review error logs.' % name
        status['form'] = ''
        status['service'] = ''
        return status

    # Get the class that implements this service.
    service_class = crits.services.manager.get_service_class(name)

    config = dict(service.config)
    cfg_form, html = service_class.generate_config_form(config)
    # This isn't a form object. It's the HTML.
    status['form'] = html
    status['service'] = service

    if post_data:
        #Populate the form with values from the POST request
        form = cfg_form(post_data)
        if form.is_valid():
            try:
                service_class.parse_config(form.cleaned_data)
            except ServiceConfigError as e:
                update_service_record(name, {"status": "misconfigured"})
                status['config_error'] = str(e)
                return status

            result = update_config(name, form.cleaned_data, user)
            if not result['success']:
                return status

            update_service_record(name, {"status": "available"})
            service = get_service_record(name)
            status['service'] = service
        else:
            status['config_error'] = form.errors
            return status

    status['success'] = True
    return status


def get_config(service_name):
    """
    Get the configuration for a service.
    """

    service = get_service_record(service_name)
    if not service:
        return None

    return service.config

def set_enabled(service_name, enabled=True, user=None):
    """
    Enable/disable a service in CRITs.
    """

    if enabled:
        logger.info("Enabling: %s" % service_name)
    else:
        logger.info("Disabling: %s" % service_name)
    service = get_service_record(service_name)
    if not service:
        return {'success': False, 'message': 'Unknown service.'}

    update_service_record(service_name, {"enabled": enabled})
    if enabled:
        url = reverse('crits-services-views-disable', args=(service_name,))
    else:
        url = reverse('crits-services-views-enable', args=(service_name,))
    return {'success': True, 'url': url}

def set_triage(service_name, enabled=True, user=None):
    """
    Enable/disable a service for running on triage (upload).
    """

    if enabled:
        logger.info("Enabling triage: %s" % service_name)
    else:
        logger.info("Disabling triage: %s" % service_name)
    service = get_service_record(service_name)
    if not service:
        return {'success': False, 'message': 'Unknown service.'}

    update_service_record(service_name, {"run_on_triage": enabled})
    if enabled:
        url = reverse('crits-services-views-disable_triage',
                      args=(service_name,))
    else:
        url = reverse('crits-services-views-enable_triage',
                      args=(service_name,))
    return {'success': True, 'url': url}

def enabled_services(status=True):
    """
    Return names of services which are enabled.
    """

    if status:
        services = find_service_records({"enabled": True, "status": "available"})
    else:
        services = find_service_records({"enabled": True})
    return [s.name for s in services]

def get_supported_services(crits_type):
    """
    Get the supported services for a type.
    """

    services = find_service_records({"enabled": True})
    for s in sorted(services, key=lambda s: s.name.lower()):
        if s.supported_types == ['all'] or crits_type in s.supported_types:
            yield s.name

def triage_services(status=True):
    """
    Return names of services set to run on triage.
    """

    if status:
        services = find_service_records({"run_on_triage": True, "status": "available"})
    else:
        services = find_service_records({"run_on_triage": True})
    return [s.name for s in services]

def delete_analysis(task_id, user):
    """
    Delete analysis results.
    """

    delete_analysis_record_by_id(task_id)

# The service pools need to be defined down here because the functions
# that are used by the services must already be defined.
if settings.SERVICE_MODEL == 'thread_pool':
    __service_thread_pool__ = ThreadPool(processes=settings.SERVICE_POOL_SIZE)
    __service_process_pool__ = None
elif settings.SERVICE_MODEL == 'process_pool':
    __service_thread_pool__ = None
    __service_process_pool__ = Pool(processes=settings.SERVICE_POOL_SIZE)
else:
    __service_thread_pool__ = None
    __service_process_pool__ = None
