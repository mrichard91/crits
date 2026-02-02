"""
Indicator queries for CRITs GraphQL API.
"""

import logging
from typing import Optional

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.indicator import IndicatorType

logger = logging.getLogger(__name__)


@strawberry.type
class IndicatorQueries:
    """Indicator-related queries."""

    @strawberry.field(description="Get a single indicator by ID")
    @require_permission("Indicator.read")
    def indicator(self, info: Info, id: str) -> Optional[IndicatorType]:
        """
        Get a single indicator by its ID.

        Args:
            id: The indicator's MongoDB ObjectId

        Returns:
            The indicator if found and accessible, None otherwise
        """
        from bson import ObjectId
        from crits.indicators.indicator import Indicator

        ctx: GraphQLContext = info.context

        try:
            # Build query with source filtering
            query = {"_id": ObjectId(id)}

            # Apply source/TLP filtering unless superuser
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            indicator = Indicator.objects(__raw__=query).first()

            if indicator:
                return IndicatorType.from_model(indicator)
            return None

        except Exception as e:
            logger.error(f"Error fetching indicator {id}: {e}")
            return None

    @strawberry.field(description="List indicators with optional filtering")
    @require_permission("Indicator.read")
    def indicators(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        ind_type: Optional[str] = None,
        value_contains: Optional[str] = None,
        status: Optional[str] = None,
        campaign: Optional[str] = None,
    ) -> list[IndicatorType]:
        """
        List indicators with optional filtering.

        Args:
            limit: Maximum number of results (default 25, max 100)
            offset: Number of results to skip for pagination
            ind_type: Filter by indicator type (e.g., "Address - ipv4-addr")
            value_contains: Filter by value containing this string (case-insensitive)
            status: Filter by status
            campaign: Filter by campaign name

        Returns:
            List of indicators matching the filters
        """
        from crits.indicators.indicator import Indicator

        ctx: GraphQLContext = info.context

        # Cap limit at 100
        limit = min(limit, 100)

        try:
            # Start with base queryset
            queryset = Indicator.objects

            # Apply source/TLP filtering unless superuser
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            # Apply optional filters
            if ind_type:
                queryset = queryset.filter(ind_type=ind_type)

            if value_contains:
                # Case-insensitive contains search
                queryset = queryset.filter(value__icontains=value_contains)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            # Order by modified date descending (most recent first)
            queryset = queryset.order_by('-modified')

            # Apply pagination
            indicators = queryset.skip(offset).limit(limit)

            return [IndicatorType.from_model(ind) for ind in indicators]

        except Exception as e:
            logger.error(f"Error listing indicators: {e}")
            return []

    @strawberry.field(description="Count indicators with optional filtering")
    @require_permission("Indicator.read")
    def indicators_count(
        self,
        info: Info,
        ind_type: Optional[str] = None,
        status: Optional[str] = None,
        campaign: Optional[str] = None,
    ) -> int:
        """
        Count indicators matching the filters.

        Args:
            ind_type: Filter by indicator type
            status: Filter by status
            campaign: Filter by campaign name

        Returns:
            Count of matching indicators
        """
        from crits.indicators.indicator import Indicator

        ctx: GraphQLContext = info.context

        try:
            queryset = Indicator.objects

            # Apply source/TLP filtering unless superuser
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if ind_type:
                queryset = queryset.filter(ind_type=ind_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting indicators: {e}")
            return 0

    @strawberry.field(description="Get distinct indicator types")
    @require_permission("Indicator.read")
    def indicator_types(self, info: Info) -> list[str]:
        """
        Get list of distinct indicator types in the database.

        Returns:
            List of indicator type strings
        """
        from crits.indicators.indicator import Indicator

        try:
            types = Indicator.objects.distinct('ind_type')
            return sorted([t for t in types if t])
        except Exception as e:
            logger.error(f"Error getting indicator types: {e}")
            return []
