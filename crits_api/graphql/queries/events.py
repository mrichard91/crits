"""
Event queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.event import EventType

logger = logging.getLogger(__name__)


@strawberry.type
class EventQueries:
    """Event-related queries."""

    @strawberry.field(description="Get a single event by ID")
    @require_permission("Event.read")
    def event(self, info: Info, id: str) -> EventType | None:
        """Get a single event by its ID."""
        from bson import ObjectId

        from crits.events.event import Event

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            event = Event.objects(__raw__=query).first()

            if event:
                return EventType.from_model(event)
            return None

        except Exception as e:
            logger.error(f"Error fetching event {id}: {e}")
            return None

    @strawberry.field(description="List events with optional filtering")
    @require_permission("Event.read")
    def events(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        title_contains: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> list[EventType]:
        """List events with optional filtering."""
        from crits.events.event import Event

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = Event.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if title_contains:
                queryset = queryset.filter(title__icontains=title_contains)

            if event_type:
                queryset = queryset.filter(event_type=event_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by("-modified")
            events = queryset.skip(offset).limit(limit)

            return [EventType.from_model(e) for e in events]

        except Exception as e:
            logger.error(f"Error listing events: {e}")
            return []

    @strawberry.field(description="Count events with optional filtering")
    @require_permission("Event.read")
    def events_count(
        self,
        info: Info,
        title_contains: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count events matching the filters."""
        from crits.events.event import Event

        ctx: GraphQLContext = info.context

        try:
            queryset = Event.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if title_contains:
                queryset = queryset.filter(title__icontains=title_contains)

            if event_type:
                queryset = queryset.filter(event_type=event_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting events: {e}")
            return 0

    @strawberry.field(description="Get distinct event types")
    @require_permission("Event.read")
    def event_types(self, info: Info) -> list[str]:
        """Get list of distinct event types."""
        from crits.events.event import Event

        try:
            types = Event.objects.distinct("event_type")
            return sorted([t for t in types if t])
        except Exception as e:
            logger.error(f"Error getting event types: {e}")
            return []
