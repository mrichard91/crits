"""Service execution pipeline.

Pipeline:
lookup service -> load TLO -> validate -> create record -> run -> update record
-> invalidate cache.
Falls back to _execute_legacy_service() for external plugins not in the modern registry.
"""

import logging
from typing import Any

from crits_api.db.service_records import get_service_record
from crits_api.worker.services.base import AnalysisContext, ServiceConfig
from crits_api.worker.services.registry import ensure_services_registered, get_service
from crits_api.worker.services.results import (
    create_analysis_record,
    mark_analysis_error,
    update_analysis_record,
)

logger = logging.getLogger(__name__)


def execute_service(
    service_name: str,
    obj_type: str,
    obj_id: str,
    username: str,
    custom_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a service on a TLO.

    Checks the modern registry first, falls back to legacy execution.

    Returns:
        Dict with 'success', 'analysis_id', and 'message' keys.
    """
    ensure_services_registered()

    service_cls = get_service(service_name)
    if service_cls:
        return _execute_modern_service(service_cls, obj_type, obj_id, username, custom_config)
    return _execute_legacy_service(service_name, obj_type, obj_id, username, custom_config)


def _execute_modern_service(
    service_cls: type,
    obj_type: str,
    obj_id: str,
    username: str,
    custom_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a modern AnalysisService."""
    result: dict[str, Any] = {"success": False, "analysis_id": "", "message": ""}

    # Instantiate service
    service = service_cls()

    # Check type support
    if not service.supports_type(obj_type):
        result["message"] = f"Service '{service.name}' does not support type '{obj_type}'"
        return result

    # Load TLO from database
    obj = _load_tlo(obj_type, obj_id)
    if obj is None:
        result["message"] = f"{obj_type} with id {obj_id} not found"
        return result

    # Create analysis record in DB
    config_dict = custom_config or {}
    try:
        analysis_id = create_analysis_record(
            service_name=service.name,
            version=service.version,
            obj_type=obj_type,
            obj_id=obj_id,
            username=username,
            config=config_dict,
        )
    except Exception as e:
        result["message"] = f"Failed to create analysis record: {e}"
        return result

    result["analysis_id"] = analysis_id

    # Build context and config
    context = AnalysisContext(
        obj=obj,
        obj_type=obj_type,
        obj_id=str(obj_id),
        username=username,
        analysis_id=analysis_id,
    )

    config = _build_config(service.config_class, custom_config, service.name)

    # Validate target
    if not service.validate_target(context):
        mark_analysis_error(analysis_id, f"Target validation failed for {obj_type}/{obj_id}")
        result["message"] = "Target validation failed"
        return result

    # Run the service
    try:
        service.run(context, config)
        status = "completed" if context.status != "error" else "error"
    except Exception as e:
        logger.exception("Service '%s' raised exception on %s/%s", service.name, obj_type, obj_id)
        context.error_log(f"Service error: {e}")
        status = "error"

    # Update the analysis record with results
    try:
        update_analysis_record(
            analysis_id=analysis_id,
            results=context.results,
            log_entries=context.log_entries,
            status=status,
        )
    except Exception as e:
        logger.error("Failed to update analysis record: %s", e)

    # Invalidate cache for this TLO type
    _invalidate_cache(obj_type)

    result["success"] = status == "completed"
    result["message"] = f"Service '{service.name}' {status}"
    return result


def _execute_legacy_service(
    service_name: str,
    obj_type: str,
    obj_id: str,
    username: str,
    custom_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fall back to the legacy service execution path.

    Calls the extracted legacy runtime without importing Django handlers.
    """
    result: dict[str, Any] = {"success": False, "analysis_id": "", "message": ""}

    try:
        from crits.services.runtime import execute_service_local

        legacy_result = execute_service_local(
            name=service_name,
            type_=obj_type,
            id_=obj_id,
            user=username,
            custom_config=custom_config or {},
        )
        result["success"] = legacy_result.get("success", False)
        result["analysis_id"] = legacy_result.get("analysis_id", "")
        result["message"] = legacy_result.get("html", "") or legacy_result.get("message", "")
    except Exception as e:
        logger.exception("Legacy service '%s' failed on %s/%s", service_name, obj_type, obj_id)
        result["message"] = str(e)

    return result


def _load_tlo(obj_type: str, obj_id: str) -> Any:
    """Load a TLO object from the database."""
    try:
        from crits.core.class_mapper import class_from_id

        return class_from_id(obj_type, obj_id)
    except Exception as e:
        logger.error("Failed to load %s/%s: %s", obj_type, obj_id, e)
        return None


def _build_config(
    config_class: type[ServiceConfig],
    custom_config: dict[str, Any] | None,
    service_name: str | None = None,
) -> ServiceConfig:
    """Build a ServiceConfig, merging DB-persisted values then runtime overrides.

    Priority (highest wins): custom_config > DB config > dataclass defaults.
    """
    merged: dict[str, Any] = {}

    # 1. Load persisted config from the service metadata record
    if service_name and config_class is not ServiceConfig:
        try:
            svc = get_service_record(service_name)
            if svc and svc.config:
                db_vals = svc.config
                # Only keep keys that are actual fields on the config class
                import dataclasses as _dc

                if _dc.is_dataclass(config_class):
                    valid_keys = {f.name for f in _dc.fields(config_class)}
                    merged.update({k: v for k, v in db_vals.items() if k in valid_keys})
        except Exception:
            logger.debug("Could not load DB config for %s", service_name)

    # 2. Runtime overrides win
    if custom_config:
        merged.update(custom_config)

    # 3. Instantiate
    if merged and config_class is not ServiceConfig:
        try:
            return config_class(**merged)
        except Exception:
            logger.debug("Could not init config class with merged config, using defaults")

    return config_class()


_TYPE_CACHE_KEY = {
    "Indicator": "indicator",
    "Actor": "actor",
    "Backdoor": "backdoor",
    "Campaign": "campaign",
    "Certificate": "certificate",
    "Domain": "domain",
    "Email": "email",
    "Event": "event",
    "Exploit": "exploit",
    "IP": "ip",
    "PCAP": "pcap",
    "RawData": "raw_data",
    "Sample": "sample",
    "Screenshot": "screenshot",
    "Signature": "signature",
    "Target": "target",
}


def _invalidate_cache(obj_type: str) -> None:
    """Invalidate the cache for a TLO type after service execution."""
    cache_key = _TYPE_CACHE_KEY.get(obj_type)
    if not cache_key:
        return
    try:
        from crits_api.cache.decorators import _fire_invalidation
        from crits_api.config import settings

        if settings.cache_enabled:
            _fire_invalidation((cache_key,))
    except Exception:
        pass  # Cache invalidation is best-effort
