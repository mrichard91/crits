"""PCAP mutation resolvers."""

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
class PCAPMutations:
    @strawberry.mutation(description="Create a new PCAP by uploading a file")
    @require_write("PCAP")
    @invalidates_sync("pcap")
    async def create_pcap(
        self,
        info: Info,
        file: Upload,
        source: str,
        filename: str | None = None,
        description: str | None = None,
    ) -> MutationResult:
        from crits.pcaps.handlers import handle_pcap_file

        ctx: GraphQLContext = info.context

        try:
            data = await file.read()  # type: ignore[attr-defined]
            upload_filename = filename or file.filename or "unknown"  # type: ignore[attr-defined]

            result = handle_pcap_file(
                upload_filename,
                data,
                source,
                user=ctx.user,
                description=description,
                tlp="red",
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "PCAP created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create PCAP"),
            )

        except Exception as e:
            logger.error(f"Error creating PCAP: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update a PCAP")
    @require_write("PCAP")
    @invalidates_object_sync("pcap")
    def update_pcap(
        self,
        info: Info,
        id: str,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update a PCAP's metadata.

        Args:
            id: The ObjectId of the PCAP to update
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
                result = description_update("PCAP", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("PCAP", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="PCAP updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating PCAP: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a PCAP")
    @require_delete("PCAP")
    @invalidates_sync("pcap")
    def delete_pcap(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete a PCAP from CRITs.

        Args:
            id: The ObjectId of the PCAP to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.pcaps.handlers import delete_pcap as django_delete_pcap
        from crits.pcaps.pcap import PCAP

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Get the PCAP to retrieve its MD5
            pcap = PCAP.objects(id=id).first()
            if not pcap:
                return MutationResult(
                    success=False,
                    message="PCAP not found",
                )

            # Delete using MD5 (as required by the Django handler)
            result = django_delete_pcap(pcap.md5, username)

            if result:
                return MutationResult(
                    success=True,
                    message="PCAP deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message="Failed to delete PCAP",
            )

        except Exception as e:
            logger.error(f"Error deleting PCAP: {e}")
            return MutationResult(success=False, message=str(e))
