"""Campaign mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class CampaignMutations:
    @strawberry.mutation(description="Create a new campaign")
    @require_write("Campaign")
    @invalidates_sync("campaign")
    def create_campaign(
        self,
        info: Info,
        name: str,
        description: str = "",
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.campaigns.handlers import add_campaign

        ctx: GraphQLContext = info.context
        assert ctx.user is not None
        username = ctx.user.username

        try:
            result = add_campaign(
                name,
                description,
                [],  # aliases
                username,
                bucket_list=bucket_list,
                ticket=ticket,
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Campaign created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create campaign"),
            )

        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update a campaign")
    @require_write("Campaign")
    @invalidates_object_sync("campaign")
    def update_campaign(
        self,
        info: Info,
        id: str,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update a campaign's metadata.

        Args:
            id: The ObjectId of the campaign to update
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
                result = description_update("Campaign", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Campaign", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Campaign updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating campaign: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a campaign")
    @require_delete("Campaign")
    @invalidates_sync("campaign")
    def delete_campaign(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete a campaign from CRITs.

        Args:
            id: The ObjectId of the campaign to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.campaigns.campaign import Campaign
        from crits.campaigns.handlers import remove_campaign

        ctx: GraphQLContext = info.context
        assert ctx.user is not None
        username = ctx.user.username

        try:
            # Get the campaign to retrieve its name
            campaign = Campaign.objects(id=id).first()
            if not campaign:
                return MutationResult(
                    success=False,
                    message="Campaign not found",
                )

            result = remove_campaign(campaign.name, username)

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message="Campaign deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to delete campaign"),
            )

        except Exception as e:
            logger.error(f"Error deleting campaign: {e}")
            return MutationResult(success=False, message=str(e))
