"""Domain mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class DomainMutations:
    @strawberry.mutation(description="Create a new domain")
    @require_write("Domain")
    def create_domain(
        self,
        info: Info,
        domain: str,
        source: str,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.domains.handlers import upsert_domain

        ctx: GraphQLContext = info.context
        assert ctx.user is not None
        username = ctx.user.username

        try:
            result = upsert_domain(
                domain,
                source,
                username=username,
                campaign=campaign,
                bucket_list=bucket_list,
                ticket=ticket,
            )

            if result.get("success"):
                obj = result.get("object")
                obj_id = str(obj.id) if obj else ""
                return MutationResult(
                    success=True,
                    message="Domain created",
                    id=obj_id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create domain"),
            )

        except Exception as e:
            logger.error(f"Error creating domain: {e}")
            return MutationResult(success=False, message=str(e))
