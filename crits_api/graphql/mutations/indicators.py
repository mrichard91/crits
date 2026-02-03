"""Indicator mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class IndicatorMutations:
    @strawberry.mutation(description="Create a new indicator")
    @require_write("Indicator")
    def create_indicator(
        self,
        info: Info,
        value: str,
        source: str,
        ind_type: str,
        threat_type: str = "unknown",
        attack_type: str = "unknown",
        description: str | None = None,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.indicators.handlers import handle_indicator_ind

        ctx: GraphQLContext = info.context

        try:
            result = handle_indicator_ind(
                value,
                source,
                ind_type,
                threat_type,
                attack_type,
                ctx.user,
                source_tlp="red",
                description=description,
                campaign=campaign,
                bucket_list=bucket_list,
                ticket=ticket,
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Indicator created"),
                    id=str(result.get("objectid", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create indicator"),
            )

        except Exception as e:
            logger.error(f"Error creating indicator: {e}")
            return MutationResult(success=False, message=str(e))
