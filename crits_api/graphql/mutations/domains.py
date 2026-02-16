"""Domain mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class DomainMutations:
    @strawberry.mutation(description="Create a new domain")
    @require_write("Domain")
    @invalidates_sync("domain")
    def create_domain(
        self,
        info: Info,
        domain: str,
        source: str,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.domains.handlers import upsert_domain

        ctx: GraphQLContext = info.context
        assert ctx.user is not None
        username = ctx.user.username

        try:
            result = upsert_domain(
                domain,
                source,
                username=username,
                campaign=campaign,
                bucket_list=bucket_list,
                ticket=ticket,
            )

            if result.get("success"):
                obj = result.get("object")
                obj_id = str(obj.id) if obj else ""
                return MutationResult(
                    success=True,
                    message="Domain created",
                    id=obj_id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create domain"),
            )

        except Exception as e:
            logger.error(f"Error creating domain: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update a domain")
    @require_write("Domain")
    @invalidates_object_sync("domain")
    def update_domain(
        self,
        info: Info,
        id: str,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update a domain's metadata.

        Args:
            id: The ObjectId of the domain to update
            description: New description
            status: New status (e.g., "In Progress", "Analyzed", "Deprecated")

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
                result = description_update("Domain", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Domain", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Domain updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating domain: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a domain")
    @require_delete("Domain")
    @invalidates_sync("domain")
    def delete_domain(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete a domain from CRITs.

        Args:
            id: The ObjectId of the domain to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.domains.domain import Domain

        ctx: GraphQLContext = info.context
        assert ctx.user is not None
        username = ctx.user.username

        try:
            domain = Domain.objects(id=id).first()
            if not domain:
                return MutationResult(
                    success=False,
                    message="Domain not found",
                )

            # Delete the domain directly (no specific handler exists)
            domain.delete(username=username)

            return MutationResult(
                success=True,
                message="Domain deleted successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error deleting domain: {e}")
            return MutationResult(success=False, message=str(e))
