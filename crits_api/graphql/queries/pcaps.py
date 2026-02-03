"""
PCAP queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.pcap import PCAPType

logger = logging.getLogger(__name__)


@strawberry.type
class PCAPQueries:
    """PCAP-related queries."""

    @strawberry.field(description="Get a single PCAP by ID")
    @require_permission("PCAP.read")
    def pcap(self, info: Info, id: str) -> PCAPType | None:
        """Get a single PCAP by its ID."""
        from bson import ObjectId

        from crits.pcaps.pcap import PCAP

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            pcap = PCAP.objects(__raw__=query).first()

            if pcap:
                return PCAPType.from_model(pcap)
            return None

        except Exception as e:
            logger.error(f"Error fetching PCAP {id}: {e}")
            return None

    @strawberry.field(description="List PCAPs with optional filtering")
    @require_permission("PCAP.read")
    def pcaps(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        filename_contains: str | None = None,
        md5: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> list[PCAPType]:
        """List PCAPs with optional filtering."""
        from crits.pcaps.pcap import PCAP

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = PCAP.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if filename_contains:
                queryset = queryset.filter(filename__icontains=filename_contains)

            if md5:
                queryset = queryset.filter(md5=md5)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by("-modified")
            pcaps = queryset.skip(offset).limit(limit)

            return [PCAPType.from_model(p) for p in pcaps]

        except Exception as e:
            logger.error(f"Error listing PCAPs: {e}")
            return []

    @strawberry.field(description="Count PCAPs with optional filtering")
    @require_permission("PCAP.read")
    def pcaps_count(
        self,
        info: Info,
        filename_contains: str | None = None,
        md5: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count PCAPs matching the filters."""
        from crits.pcaps.pcap import PCAP

        ctx: GraphQLContext = info.context

        try:
            queryset = PCAP.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if filename_contains:
                queryset = queryset.filter(filename__icontains=filename_contains)

            if md5:
                queryset = queryset.filter(md5=md5)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting PCAPs: {e}")
            return 0
