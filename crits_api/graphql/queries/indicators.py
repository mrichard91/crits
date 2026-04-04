"""
Indicator queries for CRITs GraphQL API.
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
from crits_api.db.tlo_vocabulary import DEFAULT_INDICATOR_TYPES
from crits_api.graphql.types.indicator import IndicatorType

logger = logging.getLogger(__name__)


@strawberry.type
class IndicatorQueries:
    """Indicator-related queries."""

    @strawberry.field(description="Get a single indicator by ID")
    @require_permission("Indicator.read")
    def indicator(self, info: Info, id: str) -> IndicatorType | None:
        """
        Get a single indicator by its ID.

        Args:
            id: The indicator's MongoDB ObjectId

        Returns:
            The indicator if found and accessible, None otherwise
        """
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            indicator = get_tlo_record("indicators", id, filters=source_filter)
            if indicator:
                return IndicatorType.from_model(to_model_namespace(indicator))
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
        ind_type: str | None = None,
        value_contains: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
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
        ctx: GraphQLContext = info.context

        # Cap limit at 100
        limit = min(limit, 100)

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                {"ind_type": ind_type} if ind_type else {},
                build_contains_filter("value", value_contains),
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            indicators = list_tlo_records(
                "indicators",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "value": "value",
                    "indType": "ind_type",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [
                IndicatorType.from_model(to_model_namespace(indicator)) for indicator in indicators
            ]

        except Exception as e:
            logger.error(f"Error listing indicators: {e}")
            return []

    @strawberry.field(description="Count indicators with optional filtering")
    @require_permission("Indicator.read")
    def indicators_count(
        self,
        info: Info,
        ind_type: str | None = None,
        value_contains: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """
        Count indicators matching the filters.

        Args:
            ind_type: Filter by indicator type
            value_contains: Filter by value containing this string (case-insensitive)
            status: Filter by status
            campaign: Filter by campaign name

        Returns:
            Count of matching indicators
        """
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                {"ind_type": ind_type} if ind_type else {},
                build_contains_filter("value", value_contains),
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            return count_tlo_records("indicators", filters=filters)

        except Exception as e:
            logger.error(f"Error counting indicators: {e}")
            return 0

    @strawberry.field(description="Get distinct indicator types")
    @require_permission("Indicator.read")
    def indicator_types(self, info: Info) -> list[str]:
        """Get list of distinct indicator types (vocabulary + any custom DB values)."""
        values = set(DEFAULT_INDICATOR_TYPES)
        values.update(distinct_tlo_values("indicators", "ind_type"))
        return sorted(values)
