"""Backdoor mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class BackdoorMutations:
    @strawberry.mutation(description="Create a new backdoor")
    @require_write("Backdoor")
    @invalidates_sync("backdoor")
    def create_backdoor(
        self,
        info: Info,
        name: str,
        source: str,
        description: str | None = None,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.backdoors.handlers import add_new_backdoor

        ctx: GraphQLContext = info.context

        try:
            result = add_new_backdoor(
                name,
                description=description,
                source=source,
                source_tlp="red",
                campaign=campaign,
                user=ctx.user,
                bucket_list=bucket_list,
                ticket=ticket,
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Backdoor created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create backdoor"),
            )

        except Exception as e:
            logger.error(f"Error creating backdoor: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update a backdoor")
    @require_write("Backdoor")
    @invalidates_object_sync("backdoor")
    def update_backdoor(
        self,
        info: Info,
        id: str,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update a backdoor's metadata.

        Args:
            id: The ObjectId of the backdoor to update
            name: New name for the backdoor
            description: New description
            status: New status

        Returns:
            MutationResult indicating success or failure
        """
        from crits.backdoors.handlers import set_backdoor_name
        from crits.core.handlers import description_update, status_update

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Update name if provided
            if name is not None:
                result = set_backdoor_name(id, name, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update backdoor name"),
                    )

            # Update description if provided
            if description is not None:
                result = description_update("Backdoor", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Backdoor", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Backdoor updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating backdoor: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a backdoor")
    @require_delete("Backdoor")
    @invalidates_sync("backdoor")
    def delete_backdoor(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete a backdoor from CRITs.

        Args:
            id: The ObjectId of the backdoor to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.backdoors.handlers import backdoor_remove

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            result = backdoor_remove(id, username)

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message="Backdoor deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to delete backdoor"),
            )

        except Exception as e:
            logger.error(f"Error deleting backdoor: {e}")
            return MutationResult(success=False, message=str(e))
