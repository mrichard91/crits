"""
RawData queries for CRITs GraphQL API.
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
from crits_api.graphql.types.raw_data import RawDataType

logger = logging.getLogger(__name__)


@strawberry.type
class RawDataQueries:
    """RawData-related queries."""

    @strawberry.field(description="Get a single raw data object by ID")
    @require_permission("RawData.read")
    def raw_data(self, info: Info, id: str) -> RawDataType | None:
        """Get a single raw data object by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            raw_data = get_tlo_record("raw_data", id, filters=source_filter)
            if raw_data:
                return RawDataType.from_model(to_model_namespace(raw_data))
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
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[RawDataType]:
        """List raw data objects with optional filtering."""
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("title", title_contains),
                {"data_type": data_type} if data_type else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            raw_data_list = list_tlo_records(
                "raw_data",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "title": "title",
                    "dataType": "data_type",
                    "version": "version",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [
                RawDataType.from_model(to_model_namespace(raw_data)) for raw_data in raw_data_list
            ]

        except Exception as e:
            logger.error(f"Error listing raw data: {e}")
            return []

    @strawberry.field(description="Count raw data objects with optional filtering")
    @require_permission("RawData.read")
    def raw_data_count(
        self,
        info: Info,
        title_contains: str | None = None,
        data_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count raw data objects matching the filters."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("title", title_contains),
                {"data_type": data_type} if data_type else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            return count_tlo_records("raw_data", filters=filters)

        except Exception as e:
            logger.error(f"Error counting raw data: {e}")
            return 0

    @strawberry.field(description="Get distinct raw data types")
    @require_permission("RawData.read")
    def raw_data_types(self, info: Info) -> list[str]:
        """Get list of distinct raw data types."""
        try:
            return distinct_tlo_values("raw_data", "data_type")
        except Exception as e:
            logger.error(f"Error getting raw data types: {e}")
            return []
