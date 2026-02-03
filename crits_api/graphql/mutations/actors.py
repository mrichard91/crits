"""Actor mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class ActorMutations:
    @strawberry.mutation(description="Create a new actor")
    @require_write("Actor")
    def create_actor(
        self,
        info: Info,
        name: str,
        source: str,
        description: str | None = None,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.actors.handlers import add_new_actor

        ctx: GraphQLContext = info.context

        try:
            result = add_new_actor(
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
                    message=result.get("message", "Actor created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create actor"),
            )

        except Exception as e:
            logger.error(f"Error creating actor: {e}")
            return MutationResult(success=False, message=str(e))
