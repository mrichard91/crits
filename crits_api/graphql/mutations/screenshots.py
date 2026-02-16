"""Screenshot mutation resolvers."""

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
class ScreenshotMutations:
    @strawberry.mutation(description="Create a new screenshot by uploading a file")
    @require_write("Screenshot")
    @invalidates_sync("screenshot")
    async def create_screenshot(
        self,
        info: Info,
        file: Upload,
        source: str,
        description: str | None = None,
        reference: str | None = None,
        related_type: str | None = None,
        related_id: str | None = None,
    ) -> MutationResult:
        """
        Create a new screenshot.

        Args:
            file: The screenshot image file
            source: Source of the screenshot
            description: Optional description
            reference: Optional reference URL
            related_type: Optional related TLO type
            related_id: Optional related TLO ID

        Returns:
            MutationResult indicating success or failure
        """
        from crits.screenshots.handlers import add_screenshot

        ctx: GraphQLContext = info.context

        try:
            data = await file.read()  # type: ignore[attr-defined]

            result = add_screenshot(
                description=description or "",
                tags=[],
                source=source,
                method="",
                reference=reference or "",
                tlp="",
                analyst=ctx.user,
                screenshot=data,
                screenshot_ids=[],
                oid=related_id,
                otype=related_type,
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Screenshot created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create screenshot"),
            )

        except Exception as e:
            logger.error(f"Error creating screenshot: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update a screenshot")
    @require_write("Screenshot")
    @invalidates_object_sync("screenshot")
    def update_screenshot(
        self,
        info: Info,
        id: str,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update a screenshot's metadata.

        Args:
            id: The ObjectId of the screenshot to update
            description: New description
            status: New status

        Returns:
            MutationResult indicating success or failure
        """
        from crits.core.handlers import description_update, status_update

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Update description if provided
            if description is not None:
                result = description_update("Screenshot", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Screenshot", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Screenshot updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating screenshot: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a screenshot")
    @require_delete("Screenshot")
    @invalidates_sync("screenshot")
    def delete_screenshot(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete a screenshot from CRITs.

        Args:
            id: The ObjectId of the screenshot to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.screenshots.screenshot import Screenshot

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            screenshot = Screenshot.objects(id=id).first()
            if not screenshot:
                return MutationResult(
                    success=False,
                    message="Screenshot not found",
                )

            # Delete the screenshot directly (no specific handler exists)
            screenshot.delete(username=username)

            return MutationResult(
                success=True,
                message="Screenshot deleted successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error deleting screenshot: {e}")
            return MutationResult(success=False, message=str(e))
