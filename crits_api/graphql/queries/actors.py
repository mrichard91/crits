"""
Actor queries for CRITs GraphQL API.
"""

import logging
from typing import Optional

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.actor import ActorType

logger = logging.getLogger(__name__)


@strawberry.type
class ActorQueries:
    """Actor-related queries."""

    @strawberry.field(description="Get a single actor by ID")
    @require_permission("Actor.read")
    def actor(self, info: Info, id: str) -> Optional[ActorType]:
        """Get a single actor by its ID."""
        from bson import ObjectId
        from crits.actors.actor import Actor

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            actor = Actor.objects(__raw__=query).first()

            if actor:
                return ActorType.from_model(actor)
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
        name_contains: Optional[str] = None,
        status: Optional[str] = None,
        campaign: Optional[str] = None,
    ) -> list[ActorType]:
        """List actors with optional filtering."""
        from crits.actors.actor import Actor

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = Actor.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if name_contains:
                queryset = queryset.filter(name__icontains=name_contains)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by('-modified')
            actors = queryset.skip(offset).limit(limit)

            return [ActorType.from_model(a) for a in actors]

        except Exception as e:
            logger.error(f"Error listing actors: {e}")
            return []

    @strawberry.field(description="Count actors with optional filtering")
    @require_permission("Actor.read")
    def actors_count(
        self,
        info: Info,
        status: Optional[str] = None,
        campaign: Optional[str] = None,
    ) -> int:
        """Count actors matching the filters."""
        from crits.actors.actor import Actor

        ctx: GraphQLContext = info.context

        try:
            queryset = Actor.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting actors: {e}")
            return 0
