"""
IP queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.db.tlo_records import (
    build_contains_filter,
    combine_filters,
    count_tlo_records,
    distinct_tlo_values,
    get_tlo_record,
    list_tlo_records,
    to_model_namespace,
)
from crits_api.db.tlo_vocabulary import DEFAULT_IP_TYPES
from crits_api.graphql.types.ip import IPType

logger = logging.getLogger(__name__)


@strawberry.type
class IPQueries:
    """IP-related queries."""

    @strawberry.field(description="Get a single IP by ID")
    @require_permission("IP.read")
    def ip(self, info: Info, id: str) -> IPType | None:
        """Get a single IP by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            ip_obj = get_tlo_record("ips", id, filters=source_filter)
            if ip_obj:
                return IPType.from_model(to_model_namespace(ip_obj))
            return None

        except Exception as e:
            logger.error(f"Error fetching IP {id}: {e}")
            return None

    @strawberry.field(description="List IPs with optional filtering")
    @require_permission("IP.read")
    def ips(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        ip_contains: str | None = None,
        ip_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[IPType]:
        """List IPs with optional filtering."""
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("ip", ip_contains),
                {"ip_type": ip_type} if ip_type else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            ips = list_tlo_records(
                "ips",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "ip": "ip",
                    "ipType": "ip_type",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [IPType.from_model(to_model_namespace(ip)) for ip in ips]

        except Exception as e:
            logger.error(f"Error listing IPs: {e}")
            return []

    @strawberry.field(description="Count IPs with optional filtering")
    @require_permission("IP.read")
    def ips_count(
        self,
        info: Info,
        ip_contains: str | None = None,
        ip_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count IPs matching the filters."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("ip", ip_contains),
                {"ip_type": ip_type} if ip_type else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            return count_tlo_records("ips", filters=filters)

        except Exception as e:
            logger.error(f"Error counting IPs: {e}")
            return 0

    @strawberry.field(description="Get distinct IP types")
    @require_permission("IP.read")
    def ip_types(self, info: Info) -> list[str]:
        """Get list of distinct IP types (vocabulary + any custom DB values)."""
        values = set(DEFAULT_IP_TYPES)
        values.update(distinct_tlo_values("ips", "ip_type"))
        return sorted(values)
