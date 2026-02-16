"""Sample mutation resolvers."""

import logging

import strawberry
from strawberry.file_uploads import Upload
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class SampleMutations:
    @strawberry.mutation(description="Create a new sample by uploading a file")
    @require_write("Sample")
    @invalidates_sync("sample")
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

    @strawberry.mutation(description="Update a sample's metadata")
    @require_write("Sample")
    @invalidates_object_sync("sample")
    def update_sample(
        self,
        info: Info,
        id: str,
        filename: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update a sample's metadata.

        Args:
            id: The ObjectId of the sample to update
            filename: New filename for the sample
            description: New description for the sample
            status: New status (e.g., "In Progress", "Analyzed", "Deprecated")

        Returns:
            MutationResult indicating success or failure
        """
        from crits.core.handlers import description_update, status_update
        from crits.samples.handlers import update_sample_filename

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Update filename if provided
            if filename is not None:
                result = update_sample_filename(id, filename, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update filename"),
                    )

            # Update description if provided
            if description is not None:
                result = description_update("Sample", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Sample", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Sample updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating sample: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a sample")
    @require_delete("Sample")
    @invalidates_sync("sample")
    def delete_sample(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete a sample from CRITs.

        Args:
            id: The ObjectId of the sample to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.samples.handlers import delete_sample as django_delete_sample
        from crits.samples.sample import Sample

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Get the sample to retrieve its MD5
            sample = Sample.objects(id=id).first()
            if not sample:
                return MutationResult(
                    success=False,
                    message="Sample not found",
                )

            # Delete using MD5 (as required by the Django handler)
            result = django_delete_sample(sample.md5, username)

            if result:
                return MutationResult(
                    success=True,
                    message="Sample deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message="Failed to delete sample",
            )

        except Exception as e:
            logger.error(f"Error deleting sample: {e}")
            return MutationResult(success=False, message=str(e))
