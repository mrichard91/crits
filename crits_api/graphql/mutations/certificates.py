"""Certificate mutation resolvers."""

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
class CertificateMutations:
    @strawberry.mutation(description="Create a new certificate by uploading a file")
    @require_write("Certificate")
    @invalidates_sync("certificate")
    async def create_certificate(
        self,
        info: Info,
        file: Upload,
        source: str,
        filename: str | None = None,
        description: str | None = None,
    ) -> MutationResult:
        from crits.certificates.handlers import handle_cert_file

        ctx: GraphQLContext = info.context

        try:
            data = await file.read()  # type: ignore[attr-defined]
            upload_filename = filename or file.filename or "unknown"  # type: ignore[attr-defined]

            result = handle_cert_file(
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
                    message=result.get("message", "Certificate created"),
                    id=str(result.get("id", "")),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create certificate"),
            )

        except Exception as e:
            logger.error(f"Error creating certificate: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update a certificate")
    @require_write("Certificate")
    @invalidates_object_sync("certificate")
    def update_certificate(
        self,
        info: Info,
        id: str,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update a certificate's metadata.

        Args:
            id: The ObjectId of the certificate to update
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
                result = description_update("Certificate", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Certificate", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Certificate updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating certificate: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a certificate")
    @require_delete("Certificate")
    @invalidates_sync("certificate")
    def delete_certificate(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete a certificate from CRITs.

        Args:
            id: The ObjectId of the certificate to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.certificates.certificate import Certificate
        from crits.certificates.handlers import delete_cert

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Get the certificate to retrieve its MD5
            cert = Certificate.objects(id=id).first()
            if not cert:
                return MutationResult(
                    success=False,
                    message="Certificate not found",
                )

            # Delete using MD5 (as required by the Django handler)
            result = delete_cert(cert.md5, username)

            if result:
                return MutationResult(
                    success=True,
                    message="Certificate deleted successfully",
                    id=id,
                )
            return MutationResult(
                success=False,
                message="Failed to delete certificate",
            )

        except Exception as e:
            logger.error(f"Error deleting certificate: {e}")
            return MutationResult(success=False, message=str(e))
