"""
Event queries for CRITs GraphQL API.
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
from crits_api.db.tlo_vocabulary import DEFAULT_EVENT_TYPES
from crits_api.graphql.types.event import EventType

logger = logging.getLogger(__name__)


@strawberry.type
class EventQueries:
    """Event-related queries."""

    @strawberry.field(description="Get a single event by ID")
    @require_permission("Event.read")
    def event(self, info: Info, id: str) -> EventType | None:
        """Get a single event by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            event = get_tlo_record("events", id, filters=source_filter)
            if event:
                return EventType.from_model(to_model_namespace(event))
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
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[EventType]:
        """List events with optional filtering."""
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("title", title_contains),
                {"event_type": event_type} if event_type else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            events = list_tlo_records(
                "events",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "title": "title",
                    "eventType": "event_type",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [EventType.from_model(to_model_namespace(event)) for event in events]

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
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("title", title_contains),
                {"event_type": event_type} if event_type else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            return count_tlo_records("events", filters=filters)

        except Exception as e:
            logger.error(f"Error counting events: {e}")
            return 0

    @strawberry.field(description="Get distinct event types")
    @require_permission("Event.read")
    def event_types(self, info: Info) -> list[str]:
        """Get list of distinct event types (vocabulary + any custom DB values)."""
        values = set(DEFAULT_EVENT_TYPES)
        values.update(distinct_tlo_values("events", "event_type"))
        return sorted(values)
