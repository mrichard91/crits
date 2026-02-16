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
class ServiceMutations:
    @strawberry.mutation(description="Run a service on a TLO")
    @require_authenticated
    def run_service(
        self,
        info: Info,
        service_name: str,
        obj_type: str,
        obj_id: str,
        config: str | None = None,
    ) -> MutationResult:
        """
        Run a specific service on a TLO.

        Args:
            service_name: Name of the service to run
            obj_type: The TLO type (e.g., "Sample", "Indicator")
            obj_id: The ObjectId of the TLO
            config: Optional JSON string with custom service configuration

        Returns:
            MutationResult indicating success or failure
        """
        import json

        from crits.services.handlers import run_service as django_run_service

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Parse custom config if provided
            custom_config: dict[str, Any] = {}
            if config:
                try:
                    custom_config = json.loads(config)
                except json.JSONDecodeError:
                    return MutationResult(
                        success=False,
                        message="Invalid JSON in config parameter",
                    )

            result = django_run_service(
                name=service_name,
                type_=obj_type,
                id_=obj_id,
                user=username,
                custom_config=custom_config,
            )

            if result.get("success"):
                if obj_type in _TYPE_CACHE_KEY:
                    from crits_api.config import settings

                    if settings.cache_enabled:
                        _fire_invalidation((_TYPE_CACHE_KEY[obj_type],))
                return MutationResult(
                    success=True,
                    message=f"Service '{service_name}' started successfully",
                    id=obj_id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", f"Failed to run service '{service_name}'"),
            )

        except Exception as e:
            logger.error(f"Error running service: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Run all triage services on a TLO")
    @require_authenticated
    def run_triage(
        self,
        info: Info,
        obj_type: str,
        obj_id: str,
    ) -> MutationResult:
        """
        Run all triage services on a TLO.

        Args:
            obj_type: The TLO type (e.g., "Sample", "Indicator")
            obj_id: The ObjectId of the TLO

        Returns:
            MutationResult indicating success or failure
        """
        from crits.core.class_mapper import class_from_id
        from crits.services.handlers import run_triage as django_run_triage

        ctx: GraphQLContext = info.context

        try:
            # Get the object
            obj = class_from_id(obj_type, obj_id)
            if not obj:
                return MutationResult(
                    success=False,
                    message=f"{obj_type} with id {obj_id} not found",
                )

            # Run triage (this function returns None)
            django_run_triage(obj, ctx.user)

            if obj_type in _TYPE_CACHE_KEY:
                from crits_api.config import settings

                if settings.cache_enabled:
                    _fire_invalidation((_TYPE_CACHE_KEY[obj_type],))

            return MutationResult(
                success=True,
                message="Triage services started",
                id=obj_id,
            )

        except Exception as e:
            logger.error(f"Error running triage: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.field(description="List available services")
    @require_authenticated
    def list_services(self, info: Info) -> list[ServiceInfo]:
        """
        List all available services.

        Returns:
            List of ServiceInfo objects describing available services
        """
        from crits.services.service import CRITsService

        services: list[ServiceInfo] = []

        try:
            for service in CRITsService.objects():
                # Get supported types from the service
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
