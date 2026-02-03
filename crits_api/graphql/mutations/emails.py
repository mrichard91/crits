"""Email mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_write
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class EmailMutations:
    @strawberry.mutation(description="Create a new email")
    @require_write("Email")
    def create_email(
        self,
        info: Info,
        from_address: str,
        subject: str,
        source: str,
        description: str | None = None,
        campaign: str | None = None,
        bucket_list: str | None = None,
        ticket: str | None = None,
    ) -> MutationResult:
        from crits.emails.handlers import handle_email_fields

        ctx: GraphQLContext = info.context

        try:
            data = {
                "from_address": from_address,
                "subject": subject,
                "source_name": source,
                "source_method": "",
                "source_reference": "",
                "campaign": campaign or "",
                "campaign_confidence": "low",
                "description": description or "",
                "bucket_list": bucket_list or "",
                "ticket": ticket or "",
            }

            result = handle_email_fields(data, ctx.user, "Upload")

            if result.get("status"):
                obj = result.get("object")
                obj_id = str(obj.id) if obj else ""
                return MutationResult(
                    success=True,
                    message="Email created",
                    id=obj_id,
                )
            return MutationResult(
                success=False,
                message=result.get("reason", "Failed to create email"),
            )

        except Exception as e:
            logger.error(f"Error creating email: {e}")
            return MutationResult(success=False, message=str(e))
