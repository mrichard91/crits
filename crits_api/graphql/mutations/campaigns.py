"""Campaign mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class CampaignMutations:
    @strawberry.mutation(description="Create a new campaign")
    @require_write("Campaign")
    def create_campaign(
        self,
        info: Info,
        name: str,
        description: str = "",
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.campaigns.handlers import add_campaign

        ctx: GraphQLContext = info.context
        assert ctx.user is not None
        username = ctx.user.username

        try:
            result = add_campaign(
                name,
                description,
                [],  # aliases
                username,
                bucket_list=bucket_list,
                ticket=ticket,
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Campaign created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create campaign"),
            )

        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return MutationResult(success=False, message=str(e))
