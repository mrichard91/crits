"""Event mutation resolvers."""

import contextlib
import logging
from datetime import datetime

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class EventMutations:
    @strawberry.mutation(description="Create a new event")
    @require_write("Event")
    @invalidates_sync("event")
    def create_event(
        self,
        info: Info,
        title: str,
        description: str,
        event_type: str,
        source: str,
        date: str | None = None,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.events.handlers import add_new_event

        ctx: GraphQLContext = info.context

        try:
            event_date = datetime.now()
            if date:
                with contextlib.suppress(ValueError):
                    event_date = datetime.fromisoformat(date)

            result = add_new_event(
                title,
                description,
                event_type,
                source,
                "",  # source_method
                "",  # source_reference
                "red",  # source_tlp
                event_date,
                ctx.user,
                bucket_list=bucket_list,
                ticket=ticket,
                campaign=campaign,
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Event created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create event"),
            )

        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update an event")
    @require_write("Event")
    @invalidates_object_sync("event")
    def update_event(
        self,
        info: Info,
        id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update an event's metadata.

        Args:
            id: The ObjectId of the event to update
            title: New title for the event
            description: New description
            status: New status

        Returns:
            MutationResult indicating success or failure
        """
        from crits.core.handlers import description_update, status_update
        from crits.events.handlers import update_event_title

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Update title if provided
            if title is not None:
                result = update_event_title(id, title, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update event title"),
                    )

            # Update description if provided
            if description is not None:
                result = description_update("Event", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Event", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Event updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete an event")
    @require_delete("Event")
    @invalidates_sync("event")
    def delete_event(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete an event from CRITs.

        Args:
            id: The ObjectId of the event to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.events.handlers import event_remove

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            result = event_remove(id, username)

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message="Event deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to delete event"),
            )

        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return MutationResult(success=False, message=str(e))
