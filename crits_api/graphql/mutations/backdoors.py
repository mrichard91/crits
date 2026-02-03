"""Backdoor mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class BackdoorMutations:
    @strawberry.mutation(description="Create a new backdoor")
    @require_write("Backdoor")
    def create_backdoor(
        self,
        info: Info,
        name: str,
        source: str,
        description: str | None = None,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.backdoors.handlers import add_new_backdoor

        ctx: GraphQLContext = info.context

        try:
            result = add_new_backdoor(
                name,
                description=description,
                source=source,
                source_tlp="red",
                campaign=campaign,
                user=ctx.user,
                bucket_list=bucket_list,
                ticket=ticket,
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Backdoor created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create backdoor"),
            )

        except Exception as e:
            logger.error(f"Error creating backdoor: {e}")
            return MutationResult(success=False, message=str(e))
