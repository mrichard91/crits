"""
IP queries for CRITs GraphQL API.
"""

import logging
from typing import Optional

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.ip import IPType

logger = logging.getLogger(__name__)


@strawberry.type
class IPQueries:
    """IP-related queries."""

    @strawberry.field(description="Get a single IP by ID")
    @require_permission("IP.read")
    def ip(self, info: Info, id: str) -> Optional[IPType]:
        """Get a single IP by its ID."""
        from bson import ObjectId
        from crits.ips.ip import IP

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            ip_obj = IP.objects(__raw__=query).first()

            if ip_obj:
                return IPType.from_model(ip_obj)
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
        ip_contains: Optional[str] = None,
        ip_type: Optional[str] = None,
        status: Optional[str] = None,
        campaign: Optional[str] = None,
    ) -> list[IPType]:
        """List IPs with optional filtering."""
        from crits.ips.ip import IP

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = IP.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if ip_contains:
                queryset = queryset.filter(ip__icontains=ip_contains)

            if ip_type:
                queryset = queryset.filter(ip_type=ip_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by('-modified')
            ips = queryset.skip(offset).limit(limit)

            return [IPType.from_model(ip) for ip in ips]

        except Exception as e:
            logger.error(f"Error listing IPs: {e}")
            return []

    @strawberry.field(description="Count IPs with optional filtering")
    @require_permission("IP.read")
    def ips_count(
        self,
        info: Info,
        ip_type: Optional[str] = None,
        status: Optional[str] = None,
        campaign: Optional[str] = None,
    ) -> int:
        """Count IPs matching the filters."""
        from crits.ips.ip import IP

        ctx: GraphQLContext = info.context

        try:
            queryset = IP.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if ip_type:
                queryset = queryset.filter(ip_type=ip_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting IPs: {e}")
            return 0

    @strawberry.field(description="Get distinct IP types")
    @require_permission("IP.read")
    def ip_types(self, info: Info) -> list[str]:
        """Get list of distinct IP types."""
        from crits.ips.ip import IP

        try:
            types = IP.objects.distinct('ip_type')
            return sorted([t for t in types if t])
        except Exception as e:
            logger.error(f"Error getting IP types: {e}")
            return []
