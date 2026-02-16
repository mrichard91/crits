"""IP mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class IPMutations:
    @strawberry.mutation(description="Create a new IP")
    @require_write("IP")
    @invalidates_sync("ip")
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

    @strawberry.mutation(description="Update an IP")
    @require_write("IP")
    @invalidates_object_sync("ip")
    def update_ip(
        self,
        info: Info,
        id: str,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update an IP's metadata.

        Args:
            id: The ObjectId of the IP to update
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
                result = description_update("IP", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("IP", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="IP updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating IP: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete an IP")
    @require_delete("IP")
    @invalidates_sync("ip")
    def delete_ip(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete an IP from CRITs.

        Args:
            id: The ObjectId of the IP to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.ips.ip import IP

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            ip = IP.objects(id=id).first()
            if not ip:
                return MutationResult(
                    success=False,
                    message="IP not found",
                )

            # Delete the IP directly (no specific handler exists)
            ip.delete(username=username)

            return MutationResult(
                success=True,
                message="IP deleted successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error deleting IP: {e}")
            return MutationResult(success=False, message=str(e))
