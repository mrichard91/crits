"""
Actor queries for CRITs GraphQL API.
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
from crits_api.graphql.types.actor import ActorType

logger = logging.getLogger(__name__)


@strawberry.type
class ActorQueries:
    """Actor-related queries."""

    @strawberry.field(description="Get a single actor by ID")
    @require_permission("Actor.read")
    def actor(self, info: Info, id: str) -> ActorType | None:
        """Get a single actor by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            actor = get_tlo_record("actors", id, filters=source_filter)
            if actor:
                return ActorType.from_model(to_model_namespace(actor))
            return None

        except Exception as e:
            logger.error(f"Error fetching actor {id}: {e}")
            return None

    @strawberry.field(description="List actors with optional filtering")
    @require_permission("Actor.read")
    def actors(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        name_contains: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[ActorType]:
        """List actors with optional filtering."""
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

            actors = list_tlo_records(
                "actors",
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

            return [ActorType.from_model(to_model_namespace(actor)) for actor in actors]

        except Exception as e:
            logger.error(f"Error listing actors: {e}")
            return []

    @strawberry.field(description="Count actors with optional filtering")
    @require_permission("Actor.read")
    def actors_count(
        self,
        info: Info,
        name_contains: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count actors matching the filters."""
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

            return count_tlo_records("actors", filters=filters)

        except Exception as e:
            logger.error(f"Error counting actors: {e}")
            return 0
