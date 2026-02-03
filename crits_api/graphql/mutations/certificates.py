"""Certificate mutation resolvers."""

import logging

import strawberry
from strawberry.file_uploads import Upload
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class CertificateMutations:
    @strawberry.mutation(description="Create a new certificate by uploading a file")
    @require_write("Certificate")
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
