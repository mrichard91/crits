"""RawData mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class RawDataMutations:
    @strawberry.mutation(description="Create a new raw data entry")
    @require_write("RawData")
    def create_raw_data(
        self,
        info: Info,
        title: str,
        data: str,
        data_type: str,
        source: str,
        description: str | None = None,
        tool_name: str | None = None,
        tool_version: str | None = None,
    ) -> MutationResult:
        from crits.raw_data.handlers import handle_raw_data_file

        ctx: GraphQLContext = info.context

        try:
            result = handle_raw_data_file(
                data,
                source,
                user=ctx.user,
                title=title,
                data_type=data_type,
                description=description,
                tool_name=tool_name,
                tool_version=tool_version,
                tlp="red",
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Raw data created"),
                    id=str(result.get("_id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create raw data"),
            )

        except Exception as e:
            logger.error(f"Error creating raw data: {e}")
            return MutationResult(success=False, message=str(e))
