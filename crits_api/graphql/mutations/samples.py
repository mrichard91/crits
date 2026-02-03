"""Sample mutation resolvers."""

import logging

import strawberry
from strawberry.file_uploads import Upload
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class SampleMutations:
    @strawberry.mutation(description="Create a new sample by uploading a file")
    @require_write("Sample")
    async def create_sample(
        self,
        info: Info,
        file: Upload,
        source: str,
        filename: str | None = None,
        description: str | None = None,
        campaign: str | None = None,
    ) -> MutationResult:
        from crits.samples.handlers import handle_file

        ctx: GraphQLContext = info.context

        try:
            data = await file.read()  # type: ignore[attr-defined]
            upload_filename = filename or file.filename or "unknown"  # type: ignore[attr-defined]

            result = handle_file(
                upload_filename,
                data,
                source,
                source_tlp="red",
                user=ctx.user,
                campaign=campaign,
                description=description or "",
                is_return_only_md5=False,
            )

            if result.get("success"):
                obj = result.get("object")
                obj_id = str(obj.id) if obj else ""
                return MutationResult(
                    success=True,
                    message=result.get("message", "Sample created"),
                    id=obj_id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create sample"),
            )

        except Exception as e:
            logger.error(f"Error creating sample: {e}")
            return MutationResult(success=False, message=str(e))
