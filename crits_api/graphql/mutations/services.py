"""Service mutation resolvers."""

import logging
from typing import Any

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.cache.decorators import _fire_invalidation
from crits_api.graphql.types.common import MutationResult

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

logger = logging.getLogger(__name__)


def _validate_service_config(service_name: str, values: dict[str, Any]) -> list[str]:
    """Validate config values against the service's config_class field metadata.

    Returns a list of error messages (empty if valid).
    """
    import dataclasses

    from crits_api.worker.services.registry import ensure_services_registered, get_service

    ensure_services_registered()
    svc_cls = get_service(service_name)
    if not svc_cls:
        return []  # unknown service — skip validation

    config_class = svc_cls.config_class
    if not dataclasses.is_dataclass(config_class):
        return []

    field_map = {f.name: f for f in dataclasses.fields(config_class)}
    errors: list[str] = []

    for key, val in values.items():
        f = field_map.get(key)
        if not f:
            continue

        meta = dict(f.metadata) if f.metadata else {}
        config_type = meta.get("config_type", "str")
        required = meta.get("required", False)

        # Required check
        if required and (val is None or str(val).strip() == ""):
            errors.append(f"'{key}' is required")
            continue

        # Type checks
        if config_type == "int" and val is not None and str(val).strip() != "":
            try:
                int(val)
            except (ValueError, TypeError):
                errors.append(f"'{key}' must be an integer")

        if (
            config_type == "bool"
            and val is not None
            and not isinstance(val, bool)
            and str(val).lower() not in ("true", "false", "0", "1")
        ):
            errors.append(f"'{key}' must be a boolean")

    # Check required fields that were not provided but exist on the config
    for fname, f in field_map.items():
        if fname in values:
            continue
        meta = dict(f.metadata) if f.metadata else {}
        # Only flag required fields that have no default
        if (
            meta.get("required")
            and f.default is dataclasses.MISSING
            and f.default_factory is dataclasses.MISSING
        ):
            # Only matters if the DB doesn't already have a value — skip here
            pass

    return errors


@strawberry.type
class ServiceInfo:
    """Information about an available service."""

    name: str
    description: str = ""
    enabled: bool = True
    run_on_triage: bool = False
    supported_types: list[str] = strawberry.field(default_factory=list)


@strawberry.type
class AnalysisStatusType:
    """Status of a dispatched analysis task."""

    success: bool
    message: str = ""
    analysis_id: str = ""


@strawberry.type
class ServiceMutations:
    @strawberry.mutation(description="Run a service on a TLO (async via Celery)")
    @require_authenticated
    def run_service(
        self,
        info: Info,
        service_name: str,
        obj_type: str,
        obj_id: str,
        config: str | None = None,
    ) -> AnalysisStatusType:
        """
        Run a specific service on a TLO.

        Dispatches the service to the Celery worker queue for async execution.

        Args:
            service_name: Name of the service to run
            obj_type: The TLO type (e.g., "Sample", "Indicator")
            obj_id: The ObjectId of the TLO
            config: Optional JSON string with custom service configuration

        Returns:
            AnalysisStatusType with dispatch status and analysis_id
        """
        import json

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Parse custom config if provided
            custom_config: dict[str, Any] = {}
            if config:
                try:
                    custom_config = json.loads(config)
                except json.JSONDecodeError:
                    return AnalysisStatusType(
                        success=False,
                        message="Invalid JSON in config parameter",
                    )

            # Dispatch to Celery worker
            from crits_api.worker.tasks.analysis import run_service_task

            task = run_service_task.delay(service_name, obj_type, obj_id, username, custom_config)

            if obj_type in _TYPE_CACHE_KEY:
                from crits_api.config import settings

                if settings.cache_enabled:
                    _fire_invalidation((_TYPE_CACHE_KEY[obj_type],))

            return AnalysisStatusType(
                success=True,
                message=f"Service '{service_name}' dispatched to worker",
                analysis_id=task.id,
            )

        except Exception as e:
            logger.error(f"Error dispatching service: {e}")
            return AnalysisStatusType(success=False, message=str(e))

    @strawberry.mutation(description="Run all triage services on a TLO (async via Celery)")
    @require_authenticated
    def run_triage(
        self,
        info: Info,
        obj_type: str,
        obj_id: str,
    ) -> MutationResult:
        """
        Run all triage services on a TLO.

        Dispatches a fan-out task to the Celery worker that runs each triage
        service as an independent retriable subtask.

        Args:
            obj_type: The TLO type (e.g., "Sample", "Indicator")
            obj_id: The ObjectId of the TLO

        Returns:
            MutationResult indicating success or failure
        """
        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Dispatch triage fan-out to Celery worker
            from crits_api.worker.tasks.analysis import run_triage_task

            run_triage_task.delay(obj_type, obj_id, username)

            if obj_type in _TYPE_CACHE_KEY:
                from crits_api.config import settings

                if settings.cache_enabled:
                    _fire_invalidation((_TYPE_CACHE_KEY[obj_type],))

            return MutationResult(
                success=True,
                message="Triage services dispatched to worker",
                id=obj_id,
            )

        except Exception as e:
            logger.error(f"Error dispatching triage: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.field(description="Get the status of a dispatched analysis task")
    @require_authenticated
    def analysis_status(self, info: Info, analysis_id: str) -> AnalysisStatusType:
        """
        Check the status of a running analysis by its analysis_id.

        Args:
            analysis_id: The UUID of the analysis record

        Returns:
            AnalysisStatusType with current status
        """
        try:
            from crits.services.analysis_result import AnalysisResult

            ar = AnalysisResult.objects(analysis_id=analysis_id).first()
            if not ar:
                return AnalysisStatusType(
                    success=False,
                    message=f"Analysis {analysis_id} not found",
                    analysis_id=analysis_id,
                )

            return AnalysisStatusType(
                success=ar.status == "completed",
                message=f"Status: {ar.status}",
                analysis_id=analysis_id,
            )

        except Exception as e:
            logger.error(f"Error checking analysis status: {e}")
            return AnalysisStatusType(success=False, message=str(e))

    @strawberry.mutation(description="Enable or disable a service")
    @require_authenticated
    def toggle_service_enabled(
        self, info: Info, service_name: str, enabled: bool
    ) -> MutationResult:
        """Toggle the enabled flag for a service.

        Uses upsert to create a CRITsService DB record if one doesn't exist yet.
        """
        try:
            from django.conf import settings

            col = settings.PY_DB[settings.COL_SERVICES]
            col.update_one(
                {"name": service_name},
                {"$set": {"enabled": enabled}},
                upsert=True,
            )
            logger.info("Toggled %s enabled=%s", service_name, enabled)
            return MutationResult(
                success=True,
                message=f"Service '{service_name}' {'enabled' if enabled else 'disabled'}",
            )
        except Exception as e:
            logger.error(
                "Error toggling service enabled: %s: %s", type(e).__name__, e, exc_info=True
            )
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update service configuration values")
    @require_authenticated
    def update_service_config(
        self, info: Info, service_name: str, config_json: str
    ) -> MutationResult:
        """Update persisted configuration for a service.

        Args:
            service_name: Name of the service to configure.
            config_json: JSON object of key/value pairs to set.
        """
        import json

        try:
            values = json.loads(config_json)
        except json.JSONDecodeError:
            return MutationResult(success=False, message="Invalid JSON")

        if not isinstance(values, dict):
            return MutationResult(success=False, message="config_json must be a JSON object")

        # Validate config values against service config_class metadata
        validation_errors = _validate_service_config(service_name, values)
        if validation_errors:
            return MutationResult(success=False, message="; ".join(validation_errors))

        try:
            from django.conf import settings

            col = settings.PY_DB[settings.COL_SERVICES]
            config_set = {f"config.{key}": val for key, val in values.items()}
            col.update_one(
                {"name": service_name},
                {"$set": config_set},
                upsert=True,
            )
            return MutationResult(
                success=True,
                message=f"Configuration updated for '{service_name}'",
            )
        except Exception as e:
            logger.error(f"Error updating service config: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Toggle run-on-triage flag for a service")
    @require_authenticated
    def toggle_service_triage(
        self, info: Info, service_name: str, run_on_triage: bool
    ) -> MutationResult:
        """Toggle the run_on_triage flag for a service.

        Uses upsert to create a CRITsService DB record if one doesn't exist yet.
        """
        try:
            from django.conf import settings

            col = settings.PY_DB[settings.COL_SERVICES]
            col.update_one(
                {"name": service_name},
                {"$set": {"run_on_triage": run_on_triage}},
                upsert=True,
            )
            logger.info("Toggled %s run_on_triage=%s", service_name, run_on_triage)
            return MutationResult(
                success=True,
                message=f"Service '{service_name}' triage {'enabled' if run_on_triage else 'disabled'}",
            )
        except Exception as e:
            logger.error(
                "Error toggling service triage: %s: %s", type(e).__name__, e, exc_info=True
            )
            return MutationResult(success=False, message=str(e))

    @strawberry.field(description="List available services")
    @require_authenticated
    def list_services(self, info: Info) -> list[ServiceInfo]:
        """
        List all available services (both modern and legacy).

        Returns:
            List of ServiceInfo objects describing available services
        """
        from crits.services.service import CRITsService

        services: list[ServiceInfo] = []
        seen_names: set[str] = set()

        # Modern registered services
        try:
            from crits_api.worker.services.registry import (
                ensure_services_registered,
                get_all_services,
            )

            ensure_services_registered()
            for name, cls in get_all_services().items():
                services.append(
                    ServiceInfo(
                        name=cls.name,
                        description=cls.description,
                        enabled=True,
                        run_on_triage=cls.run_on_triage,
                        supported_types=list(cls.supported_types),
                    )
                )
                seen_names.add(name)
        except Exception as e:
            logger.debug(f"Could not load modern services: {e}")

        # Legacy DB services (not already covered by modern)
        try:
            for service in CRITsService.objects():
                if service.name in seen_names:
                    continue
                supported_types: list[str] = []
                if hasattr(service, "supported_types"):
                    supported_types = list(service.supported_types or [])

                services.append(
                    ServiceInfo(
                        name=service.name,
                        description=getattr(service, "description", "") or "",
                        enabled=getattr(service, "enabled", True),
                        run_on_triage=getattr(service, "run_on_triage", False),
                        supported_types=supported_types,
                    )
                )
        except Exception as e:
            logger.error(f"Error listing services: {e}")

        return services
