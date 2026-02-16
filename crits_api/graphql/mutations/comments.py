"""Comment mutation resolvers."""

import logging
from datetime import datetime

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.cache.decorators import _fire_invalidation
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)

_TYPE_CACHE_KEY = {
    "Indicator": "indicator",
    "Actor": "actor",
    "Backdoor": "backdoor",
    "Campaign": "campaign",
    "Certificate": "certificate",
    "Domain": "domain",
    "Email": "email",
    "Event": "event",
    "Exploit": "exploit",
    "IP": "ip",
    "PCAP": "pcap",
    "RawData": "raw_data",
    "Sample": "sample",
    "Screenshot": "screenshot",
    "Signature": "signature",
    "Target": "target",
}


def _invalidate_comment_target(obj_type: str) -> None:
    from crits_api.config import settings

    if settings.cache_enabled and obj_type in _TYPE_CACHE_KEY:
        _fire_invalidation((_TYPE_CACHE_KEY[obj_type],))


@strawberry.type
class CommentMutations:
    @strawberry.mutation(description="Add a comment to a TLO")
    @require_authenticated
    def add_comment(
        self,
        info: Info,
        obj_type: str,
        obj_id: str,
        comment: str,
        parent_date: str | None = None,
        parent_analyst: str | None = None,
    ) -> MutationResult:
        """
        Add a new comment to a TLO.

        Args:
            obj_type: The TLO type (e.g., "Sample", "Indicator")
            obj_id: The ObjectId of the TLO
            comment: The comment text
            parent_date: If replying, the ISO date of the parent comment
            parent_analyst: If replying, the analyst who wrote the parent comment

        Returns:
            MutationResult indicating success or failure
        """
        from crits.comments.handlers import comment_add

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Build the cleaned_data dict expected by the handler
            cleaned_data = {
                "comment": comment,
            }

            # Determine if this is a reply
            method = ""
            if parent_date and parent_analyst:
                method = "reply"
                cleaned_data["parent_date"] = parent_date
                cleaned_data["parent_analyst"] = parent_analyst

            # Empty subscription dict - comments don't use subscriptions via API
            subscr: dict[str, str] = {}

            result = comment_add(
                cleaned_data,
                obj_type,
                obj_id,
                method,
                subscr,
                username,
            )

            if result.get("success"):
                _invalidate_comment_target(obj_type)
                return MutationResult(
                    success=True,
                    message=result.get("message", "Comment added"),
                    id=obj_id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to add comment"),
            )

        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Edit an existing comment")
    @require_authenticated
    def edit_comment(
        self,
        info: Info,
        obj_type: str,
        obj_id: str,
        comment_date: str,
        comment: str,
    ) -> MutationResult:
        """
        Edit an existing comment.

        Args:
            obj_type: The TLO type (e.g., "Sample", "Indicator")
            obj_id: The ObjectId of the TLO
            comment_date: The ISO date of the comment to edit
            comment: The new comment text

        Returns:
            MutationResult indicating success or failure
        """
        from crits.comments.handlers import comment_update

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Build the cleaned_data dict expected by the handler
            cleaned_data = {
                "comment": comment,
                "date": comment_date,
            }

            # Empty subscription dict
            subscr: dict[str, str] = {}

            result = comment_update(
                cleaned_data,
                obj_type,
                obj_id,
                subscr,
                username,
            )

            # comment_update returns an HttpResponse, check for success
            if hasattr(result, "status_code"):
                if result.status_code == 200:
                    _invalidate_comment_target(obj_type)
                    return MutationResult(
                        success=True,
                        message="Comment updated",
                        id=obj_id,
                    )
                return MutationResult(
                    success=False,
                    message="Failed to update comment",
                )

            # Handle dict response
            if isinstance(result, dict):
                if result.get("success"):
                    _invalidate_comment_target(obj_type)
                    return MutationResult(
                        success=True,
                        message=result.get("message", "Comment updated"),
                        id=obj_id,
                    )
                return MutationResult(
                    success=False,
                    message=result.get("message", "Failed to update comment"),
                )

            _invalidate_comment_target(obj_type)
            return MutationResult(
                success=True,
                message="Comment updated",
                id=obj_id,
            )

        except Exception as e:
            logger.error(f"Error updating comment: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a comment")
    @require_authenticated
    def delete_comment(
        self,
        info: Info,
        obj_id: str,
        comment_date: str,
    ) -> MutationResult:
        """
        Delete a comment from a TLO.

        Args:
            obj_id: The ObjectId of the TLO containing the comment
            comment_date: The ISO date of the comment to delete

        Returns:
            MutationResult indicating success or failure
        """
        from crits.comments.handlers import comment_remove

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Parse the date string to datetime
            date = datetime.fromisoformat(comment_date.replace("Z", "+00:00"))

            result = comment_remove(obj_id, username, date)

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Comment deleted"),
                    id=obj_id,
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to delete comment"),
            )

        except Exception as e:
            logger.error(f"Error deleting comment: {e}")
            return MutationResult(success=False, message=str(e))
