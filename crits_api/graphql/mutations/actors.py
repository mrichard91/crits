"""Actor mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class ActorMutations:
    @strawberry.mutation(description="Create a new actor")
    @require_write("Actor")
    @invalidates_sync("actor")
    def create_actor(
        self,
        info: Info,
        name: str,
        source: str,
        description: str | None = None,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.actors.handlers import add_new_actor

        ctx: GraphQLContext = info.context

        try:
            result = add_new_actor(
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
                    message=result.get("message", "Actor created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create actor"),
            )

        except Exception as e:
            logger.error(f"Error creating actor: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update an actor")
    @require_write("Actor")
    @invalidates_object_sync("actor")
    def update_actor(
        self,
        info: Info,
        id: str,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update an actor's metadata.

        Args:
            id: The ObjectId of the actor to update
            name: New name for the actor
            description: New description
            status: New status

        Returns:
            MutationResult indicating success or failure
        """
        from crits.actors.handlers import set_actor_name
        from crits.core.handlers import description_update, status_update

        ctx: GraphQLContext = info.context

        try:
            # Update name if provided
            if name is not None:
                result = set_actor_name(id, name, ctx.user)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update actor name"),
                    )

            username = ctx.user.username if ctx.user else "unknown"

            # Update description if provided
            if description is not None:
                result = description_update("Actor", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Actor", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Actor updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating actor: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete an actor")
    @require_delete("Actor")
    @invalidates_sync("actor")
    def delete_actor(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete an actor from CRITs.

        Args:
            id: The ObjectId of the actor to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.actors.handlers import actor_remove

        ctx: GraphQLContext = info.context

        try:
            result = actor_remove(id, ctx.user)

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message="Actor deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to delete actor"),
            )

        except Exception as e:
            logger.error(f"Error deleting actor: {e}")
            return MutationResult(success=False, message=str(e))
