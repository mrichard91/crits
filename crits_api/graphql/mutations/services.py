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
