"""
Backdoor queries for CRITs GraphQL API.
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
    get_tlo_record,
    list_tlo_records,
    to_model_namespace,
)
from crits_api.graphql.types.backdoor import BackdoorType

logger = logging.getLogger(__name__)


@strawberry.type
class BackdoorQueries:
    """Backdoor-related queries."""

    @strawberry.field(description="Get a single backdoor by ID")
    @require_permission("Backdoor.read")
    def backdoor(self, info: Info, id: str) -> BackdoorType | None:
        """Get a single backdoor by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            backdoor = get_tlo_record("backdoors", id, filters=source_filter)
            if backdoor:
                return BackdoorType.from_model(to_model_namespace(backdoor))
            return None

        except Exception as e:
            logger.error(f"Error fetching backdoor {id}: {e}")
            return None

    @strawberry.field(description="List backdoors with optional filtering")
    @require_permission("Backdoor.read")
    def backdoors(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        name_contains: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[BackdoorType]:
        """List backdoors with optional filtering."""
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("name", name_contains),
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            backdoors = list_tlo_records(
                "backdoors",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "name": "name",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [BackdoorType.from_model(to_model_namespace(backdoor)) for backdoor in backdoors]

        except Exception as e:
            logger.error(f"Error listing backdoors: {e}")
            return []

    @strawberry.field(description="Count backdoors with optional filtering")
    @require_permission("Backdoor.read")
    def backdoors_count(
        self,
        info: Info,
        name_contains: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count backdoors matching the filters."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("name", name_contains),
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            return count_tlo_records("backdoors", filters=filters)

        except Exception as e:
            logger.error(f"Error counting backdoors: {e}")
            return 0
