"""Signature mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class SignatureMutations:
    @strawberry.mutation(description="Create a new signature")
    @require_write("Signature")
    def create_signature(
        self,
        info: Info,
        title: str,
        data: str,
        data_type: str,
        source: str,
        description: str | None = None,
        data_type_min_version: str | None = None,
        data_type_max_version: str | None = None,
    ) -> MutationResult:
        from crits.signatures.handlers import handle_signature_file

        ctx: GraphQLContext = info.context

        try:
            result = handle_signature_file(
                data.encode("utf-8"),
                source,
                user=ctx.user,
                title=title,
                data_type=data_type,
                description=description,
                data_type_min_version=data_type_min_version,
                data_type_max_version=data_type_max_version,
                source_tlp="red",
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Signature created"),
                    id=str(result.get("_id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create signature"),
            )

        except Exception as e:
            logger.error(f"Error creating signature: {e}")
            return MutationResult(success=False, message=str(e))
