"""PCAP mutation resolvers."""

import logging

import strawberry
from strawberry.file_uploads import Upload
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class PCAPMutations:
    @strawberry.mutation(description="Create a new PCAP by uploading a file")
    @require_write("PCAP")
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
