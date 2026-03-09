"""Comment query resolvers."""

import logging
from typing import Any

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_authenticated

logger = logging.getLogger(__name__)


@strawberry.type
class CommentType:
    """A comment on a TLO."""

    id: str
    comment: str
    analyst: str
    created: str
    edit_date: str
    parent_date: str | None = None
    parent_analyst: str | None = None

    @classmethod
    def from_model(cls, comment: Any) -> "CommentType":
        """Create CommentType from Comment MongoEngine model."""
        parent_date = None
        parent_analyst = None
        if hasattr(comment, "parent") and comment.parent:
            pd = getattr(comment.parent, "date", None)
            if pd:
                parent_date = pd.isoformat()
            parent_analyst = getattr(comment.parent, "analyst", None) or None

        created = getattr(comment, "created", None)
        edit_date = getattr(comment, "edit_date", None)

        return cls(
            id=str(comment.id),
            comment=getattr(comment, "comment", "") or "",
            analyst=getattr(comment, "analyst", "") or "",
            created=created.isoformat() if created else "",
            edit_date=edit_date.isoformat() if edit_date else "",
            parent_date=parent_date,
            parent_analyst=parent_analyst,
        )


@strawberry.type
class CommentQueries:
    @strawberry.field(description="Get comments for a TLO")
    @require_authenticated
    def comments(
        self,
        info: Info,
        obj_type: str,
        obj_id: str,
    ) -> list[CommentType]:
        """
        Get all comments for a given TLO.

        Args:
            obj_type: The TLO type (e.g., "Sample", "Indicator")
            obj_id: The ObjectId of the TLO

        Returns:
            List of comments ordered by creation date
        """
        from bson import ObjectId

        from crits.comments.comment import Comment

        try:
            results = Comment.objects(obj_id=ObjectId(obj_id), obj_type=obj_type).order_by(
                "+created"
            )
            return [CommentType.from_model(c) for c in results]
        except Exception as e:
            logger.error(f"Error fetching comments: {e}")
            return []
