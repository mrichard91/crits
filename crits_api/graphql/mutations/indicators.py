"""Indicator mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class IndicatorMutations:
    @strawberry.mutation(description="Create a new indicator")
    @require_write("Indicator")
    @invalidates_sync("indicator")
    def create_indicator(
        self,
        info: Info,
        value: str,
        source: str,
        ind_type: str,
        threat_type: str = "unknown",
        attack_type: str = "unknown",
        description: str | None = None,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.indicators.handlers import handle_indicator_ind

        ctx: GraphQLContext = info.context

        try:
            result = handle_indicator_ind(
                value,
                source,
                ind_type,
                threat_type,
                attack_type,
                ctx.user,
                source_tlp="red",
                description=description,
                campaign=campaign,
                bucket_list=bucket_list,
                ticket=ticket,
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Indicator created"),
                    id=str(result.get("objectid", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create indicator"),
            )

        except Exception as e:
            logger.error(f"Error creating indicator: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update an indicator")
    @require_write("Indicator")
    @invalidates_object_sync("indicator")
    def update_indicator(
        self,
        info: Info,
        id: str,
        ind_type: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update an indicator's metadata.

        Args:
            id: The ObjectId of the indicator to update
            ind_type: New indicator type
            description: New description
            status: New status (e.g., "In Progress", "Analyzed", "Deprecated")

        Returns:
            MutationResult indicating success or failure
        """
        from crits.core.handlers import description_update, status_update
        from crits.indicators.handlers import set_indicator_type

        ctx: GraphQLContext = info.context

        try:
            # Update indicator type if provided
            if ind_type is not None:
                result = set_indicator_type(id, ind_type, ctx.user)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update indicator type"),
                    )

            username = ctx.user.username if ctx.user else "unknown"

            # Update description if provided
            if description is not None:
                result = description_update("Indicator", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Indicator", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Indicator updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating indicator: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete an indicator")
    @require_delete("Indicator")
    @invalidates_sync("indicator")
    def delete_indicator(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete an indicator from CRITs.

        Args:
            id: The ObjectId of the indicator to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.indicators.handlers import indicator_remove

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            result = indicator_remove(id, username)

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message="Indicator deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message=str(result.get("message", "Failed to delete indicator")),
            )

        except Exception as e:
            logger.error(f"Error deleting indicator: {e}")
            return MutationResult(success=False, message=str(e))
