"""Event mutation resolvers."""

import contextlib
import logging
from datetime import datetime

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class EventMutations:
    @strawberry.mutation(description="Create a new event")
    @require_write("Event")
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
