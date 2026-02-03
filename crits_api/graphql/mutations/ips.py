"""IP mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class IPMutations:
    @strawberry.mutation(description="Create a new IP")
    @require_write("IP")
    def create_ip(
        self,
        info: Info,
        ip_address: str,
        ip_type: str,
        source: str,
        description: str | None = None,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.ips.handlers import ip_add_update

        ctx: GraphQLContext = info.context

        try:
            result = ip_add_update(
                ip_address,
                ip_type,
                source=source,
                source_tlp="red",
                user=ctx.user,
                campaign=campaign,
                bucket_list=bucket_list,
                ticket=ticket,
                description=description or "",
            )

            if result.get("success"):
                obj = result.get("object")
                obj_id = str(obj.id) if obj else ""
                return MutationResult(
                    success=True,
                    message=result.get("message", "IP created"),
                    id=obj_id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create IP"),
            )

        except Exception as e:
            logger.error(f"Error creating IP: {e}")
            return MutationResult(success=False, message=str(e))
