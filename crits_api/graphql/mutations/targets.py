"""Target mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class TargetMutations:
    @strawberry.mutation(description="Create a new target")
    @require_write("Target")
    @invalidates_sync("target")
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

    @strawberry.mutation(description="Update a target")
    @require_write("Target")
    @invalidates_object_sync("target")
    def update_target(
        self,
        info: Info,
        id: str,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update a target's metadata.

        Args:
            id: The ObjectId of the target to update
            description: New description
            status: New status

        Returns:
            MutationResult indicating success or failure
        """
        from crits.core.handlers import description_update, status_update

        ctx: GraphQLContext = info.context
        assert ctx.user is not None
        username = ctx.user.username

        try:
            # Update description if provided
            if description is not None:
                result = description_update("Target", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Target", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Target updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating target: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a target")
    @require_delete("Target")
    @invalidates_sync("target")
    def delete_target(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete a target from CRITs.

        Args:
            id: The ObjectId of the target to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.targets.handlers import remove_target
        from crits.targets.target import Target

        ctx: GraphQLContext = info.context
        assert ctx.user is not None
        username = ctx.user.username

        try:
            # Get the target to retrieve its email address
            target = Target.objects(id=id).first()
            if not target:
                return MutationResult(
                    success=False,
                    message="Target not found",
                )

            result = remove_target(email_address=target.email_address, analyst=username)

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message="Target deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to delete target"),
            )

        except Exception as e:
            logger.error(f"Error deleting target: {e}")
            return MutationResult(success=False, message=str(e))
