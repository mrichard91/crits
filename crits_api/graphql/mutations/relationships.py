"""Relationship mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)


@strawberry.type
class RelationshipMutations:
    @strawberry.mutation(description="Add a relationship between two TLOs")
    @require_authenticated
    def add_relationship(
        self,
        info: Info,
        left_type: str,
        left_id: str,
        right_type: str,
        right_id: str,
        rel_type: str,
        rel_confidence: str = "unknown",
        rel_reason: str = "",
    ) -> MutationResult:
        """
        Create a relationship between two TLOs.

        Args:
            left_type: Type of the source TLO (e.g., "Indicator")
            left_id: MongoDB ObjectId of the source TLO
            right_type: Type of the target TLO (e.g., "Sample")
            right_id: MongoDB ObjectId of the target TLO
            rel_type: Relationship label (e.g., "Related To")
            rel_confidence: Confidence level (unknown, low, medium, high)
            rel_reason: Optional reason for the relationship

        Returns:
            MutationResult indicating success or failure
        """
        from crits.relationships.handlers import forge_relationship

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            result = forge_relationship(
                type_=left_type,
                id_=left_id,
                right_type=right_type,
                right_id=right_id,
                rel_type=rel_type,
                user=username,
                rel_confidence=rel_confidence,
                rel_reason=rel_reason,
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Relationship created"),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to create relationship"),
            )

        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Remove a relationship between two TLOs")
    @require_authenticated
    def remove_relationship(
        self,
        info: Info,
        left_type: str,
        left_id: str,
        right_type: str,
        right_id: str,
        rel_type: str,
    ) -> MutationResult:
        """
        Remove a relationship between two TLOs.

        Args:
            left_type: Type of the source TLO (e.g., "Indicator")
            left_id: MongoDB ObjectId of the source TLO
            right_type: Type of the target TLO (e.g., "Sample")
            right_id: MongoDB ObjectId of the target TLO
            rel_type: Relationship label to match (e.g., "Related To")

        Returns:
            MutationResult indicating success or failure
        """
        from crits.relationships.handlers import delete_relationship

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            result = delete_relationship(
                left_type=left_type,
                left_id=left_id,
                right_type=right_type,
                right_id=right_id,
                rel_type=rel_type,
                analyst=username,
                get_rels=False,
            )

            if result.get("success"):
                return MutationResult(
                    success=True,
                    message=result.get("message", "Relationship removed"),
                )
            return MutationResult(
                success=False,
                message=result.get("message", "Failed to remove relationship"),
            )

        except Exception as e:
            logger.error(f"Error removing relationship: {e}")
            return MutationResult(success=False, message=str(e))
