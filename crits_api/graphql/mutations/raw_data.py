"""RawData mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class RawDataMutations:
    @strawberry.mutation(description="Create a new raw data entry")
    @require_write("RawData")
    @invalidates_sync("raw_data")
    def create_raw_data(
        self,
        info: Info,
        title: str,
        data: str,
        data_type: str,
        source: str,
        description: str | None = None,
        tool_name: str | None = None,
        tool_version: str | None = None,
    ) -> MutationResult:
        from crits.raw_data.handlers import handle_raw_data_file

        ctx: GraphQLContext = info.context

        try:
            result = handle_raw_data_file(
                data,
                source,
                user=ctx.user,
                title=title,
                data_type=data_type,
                description=description,
                tool_name=tool_name,
                tool_version=tool_version,
                tlp="red",
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Raw data created"),
                    id=str(result.get("_id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create raw data"),
            )

        except Exception as e:
            logger.error(f"Error creating raw data: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update raw data")
    @require_write("RawData")
    @invalidates_object_sync("raw_data")
    def update_raw_data(
        self,
        info: Info,
        id: str,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update raw data metadata.

        Args:
            id: The ObjectId of the raw data to update
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
                result = description_update("RawData", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("RawData", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Raw data updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating raw data: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete raw data")
    @require_delete("RawData")
    @invalidates_sync("raw_data")
    def delete_raw_data(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete raw data from CRITs.

        Args:
            id: The ObjectId of the raw data to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.raw_data.handlers import delete_raw_data as django_delete_raw_data

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            result = django_delete_raw_data(id, username)

            if result:
                return MutationResult(
                    success=True,
                    message="Raw data deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message="Failed to delete raw data",
            )

        except Exception as e:
            logger.error(f"Error deleting raw data: {e}")
            return MutationResult(success=False, message=str(e))
