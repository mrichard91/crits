"""Target mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class TargetMutations:
    @strawberry.mutation(description="Create a new target")
    @require_write("Target")
    def create_target(
        self,
        info: Info,
        email_address: str,
        description: str | None = None,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.targets.handlers import upsert_target

        ctx: GraphQLContext = info.context
        assert ctx.user is not None
        username = ctx.user.username

        try:
            data = {
                "email_address": email_address,
                "campaign": campaign or "",
                "bucket_list": bucket_list or "",
                "ticket": ticket or "",
            }

            result = upsert_target(data, username)

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Target created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create target"),
            )

        except Exception as e:
            logger.error(f"Error creating target: {e}")
            return MutationResult(success=False, message=str(e))
