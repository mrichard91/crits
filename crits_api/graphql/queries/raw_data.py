"""
RawData queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.raw_data import RawDataType

logger = logging.getLogger(__name__)


@strawberry.type
class RawDataQueries:
    """RawData-related queries."""

    @strawberry.field(description="Get a single raw data object by ID")
    @require_permission("RawData.read")
    def raw_data(self, info: Info, id: str) -> RawDataType | None:
        """Get a single raw data object by its ID."""
        from bson import ObjectId

        from crits.raw_data.raw_data import RawData

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            raw_data = RawData.objects(__raw__=query).first()

            if raw_data:
                return RawDataType.from_model(raw_data)
            return None

        except Exception as e:
            logger.error(f"Error fetching raw data {id}: {e}")
            return None

    @strawberry.field(description="List raw data objects with optional filtering")
    @require_permission("RawData.read")
    def raw_data_list(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        title_contains: str | None = None,
        data_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> list[RawDataType]:
        """List raw data objects with optional filtering."""
        from crits.raw_data.raw_data import RawData

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = RawData.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if title_contains:
                queryset = queryset.filter(title__icontains=title_contains)

            if data_type:
                queryset = queryset.filter(data_type=data_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by("-modified")
            raw_data_list = queryset.skip(offset).limit(limit)

            return [RawDataType.from_model(rd) for rd in raw_data_list]

        except Exception as e:
            logger.error(f"Error listing raw data: {e}")
            return []

    @strawberry.field(description="Count raw data objects with optional filtering")
    @require_permission("RawData.read")
    def raw_data_count(
        self,
        info: Info,
        data_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count raw data objects matching the filters."""
        from crits.raw_data.raw_data import RawData

        ctx: GraphQLContext = info.context

        try:
            queryset = RawData.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if data_type:
                queryset = queryset.filter(data_type=data_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting raw data: {e}")
            return 0

    @strawberry.field(description="Get distinct raw data types")
    @require_permission("RawData.read")
    def raw_data_types(self, info: Info) -> list[str]:
        """Get list of distinct raw data types."""
        from crits.raw_data.raw_data import RawData

        try:
            types = RawData.objects.distinct("data_type")
            return sorted([t for t in types if t])
        except Exception as e:
            logger.error(f"Error getting raw data types: {e}")
            return []
