"""Signature mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class SignatureMutations:
    @strawberry.mutation(description="Create a new signature")
    @require_write("Signature")
    @invalidates_sync("signature")
    def create_signature(
        self,
        info: Info,
        title: str,
        data: str,
        data_type: str,
        source: str,
        description: str | None = None,
        data_type_min_version: str | None = None,
        data_type_max_version: str | None = None,
    ) -> MutationResult:
        from crits.signatures.handlers import handle_signature_file

        ctx: GraphQLContext = info.context

        try:
            result = handle_signature_file(
                data.encode("utf-8"),
                source,
                user=ctx.user,
                title=title,
                data_type=data_type,
                description=description,
                data_type_min_version=data_type_min_version,
                data_type_max_version=data_type_max_version,
                source_tlp="red",
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Signature created"),
                    id=str(result.get("_id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create signature"),
            )

        except Exception as e:
            logger.error(f"Error creating signature: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update a signature")
    @require_write("Signature")
    @invalidates_object_sync("signature")
    def update_signature(
        self,
        info: Info,
        id: str,
        data_type: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update a signature's metadata.

        Args:
            id: The ObjectId of the signature to update
            data_type: New data type for the signature
            description: New description
            status: New status

        Returns:
            MutationResult indicating success or failure
        """
        from crits.core.handlers import description_update, status_update
        from crits.signatures.handlers import update_signature_type

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Update data type if provided
            if data_type is not None:
                result = update_signature_type("Signature", id, data_type, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update signature type"),
                    )

            # Update description if provided
            if description is not None:
                result = description_update("Signature", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Signature", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Signature updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating signature: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a signature")
    @require_delete("Signature")
    @invalidates_sync("signature")
    def delete_signature(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete a signature from CRITs.

        Args:
            id: The ObjectId of the signature to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.signatures.handlers import delete_signature as django_delete_signature

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            result = django_delete_signature(id, username)

            if result:
                return MutationResult(
                    success=True,
                    message="Signature deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message="Failed to delete signature",
            )

        except Exception as e:
            logger.error(f"Error deleting signature: {e}")
            return MutationResult(success=False, message=str(e))
