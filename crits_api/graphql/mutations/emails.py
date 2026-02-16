"""Email mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_delete, require_write
from crits_api.cache.decorators import invalidates_object_sync, invalidates_sync
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class EmailMutations:
    @strawberry.mutation(description="Create a new email")
    @require_write("Email")
    @invalidates_sync("email")
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

    @strawberry.mutation(description="Update an email")
    @require_write("Email")
    @invalidates_object_sync("email")
    def update_email(
        self,
        info: Info,
        id: str,
        description: str | None = None,
        status: str | None = None,
    ) -> MutationResult:
        """
        Update an email's metadata.

        Args:
            id: The ObjectId of the email to update
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
                result = description_update("Email", id, description, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update description"),
                    )

            # Update status if provided
            if status is not None:
                result = status_update("Email", id, status, username)
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update status"),
                    )

            return MutationResult(
                success=True,
                message="Email updated successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error updating email: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete an email")
    @require_delete("Email")
    @invalidates_sync("email")
    def delete_email(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """
        Delete an email from CRITs.

        Args:
            id: The ObjectId of the email to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.emails.email import Email

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            email = Email.objects(id=id).first()
            if not email:
                return MutationResult(
                    success=False,
                    message="Email not found",
                )

            # Delete the email directly (no specific handler exists)
            email.delete(username=username)

            return MutationResult(
                success=True,
                message="Email deleted successfully",
                id=id,
            )

        except Exception as e:
            logger.error(f"Error deleting email: {e}")
            return MutationResult(success=False, message=str(e))
