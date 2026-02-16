"""Relationship mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.cache.decorators import _fire_invalidation
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)

# Mapping of TLO type to cache key prefix
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


def _invalidate_relationship_types(left_type: str, right_type: str) -> None:
    """Invalidate cache for both sides of a relationship."""
    from crits_api.config import settings

    if not settings.cache_enabled:
        return
    types = set()
    if left_type in _TYPE_CACHE_KEY:
        types.add(_TYPE_CACHE_KEY[left_type])
    if right_type in _TYPE_CACHE_KEY:
        types.add(_TYPE_CACHE_KEY[right_type])
    if types:
        _fire_invalidation(tuple(types))


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
                _invalidate_relationship_types(left_type, right_type)
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
                _invalidate_relationship_types(left_type, right_type)
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

    @strawberry.mutation(description="Update a relationship between two TLOs")
    @require_authenticated
    def update_relationship(
        self,
        info: Info,
        left_type: str,
        left_id: str,
        right_type: str,
        right_id: str,
        rel_type: str,
        new_rel_type: str | None = None,
        new_confidence: str | None = None,
        new_reason: str | None = None,
    ) -> MutationResult:
        """
        Update a relationship between two TLOs.

        Args:
            left_type: Type of the source TLO (e.g., "Indicator")
            left_id: MongoDB ObjectId of the source TLO
            right_type: Type of the target TLO (e.g., "Sample")
            right_id: MongoDB ObjectId of the target TLO
            rel_type: Current relationship label (e.g., "Related To")
            new_rel_type: New relationship type (if changing)
            new_confidence: New confidence level (unknown, low, medium, high)
            new_reason: New reason for the relationship

        Returns:
            MutationResult indicating success or failure
        """
        from crits.relationships.handlers import (
            update_relationship_confidences,
            update_relationship_reasons,
            update_relationship_types,
        )

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        try:
            # Update relationship type if provided
            if new_rel_type is not None:
                result = update_relationship_types(
                    left_type=left_type,
                    left_id=left_id,
                    right_type=right_type,
                    right_id=right_id,
                    rel_type=rel_type,
                    new_type=new_rel_type,
                    analyst=username,
                )
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update relationship type"),
                    )
                # Use the new type for subsequent updates
                rel_type = new_rel_type

            # Update confidence if provided
            if new_confidence is not None:
                result = update_relationship_confidences(
                    left_type=left_type,
                    left_id=left_id,
                    right_type=right_type,
                    right_id=right_id,
                    rel_type=rel_type,
                    new_confidence=new_confidence,
                    analyst=username,
                )
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update relationship confidence"),
                    )

            # Update reason if provided
            if new_reason is not None:
                result = update_relationship_reasons(
                    left_type=left_type,
                    left_id=left_id,
                    right_type=right_type,
                    right_id=right_id,
                    rel_type=rel_type,
                    new_reason=new_reason,
                    analyst=username,
                )
                if not result.get("success"):
                    return MutationResult(
                        success=False,
                        message=result.get("message", "Failed to update relationship reason"),
                    )

            _invalidate_relationship_types(left_type, right_type)
            return MutationResult(
                success=True,
                message="Relationship updated successfully",
            )

        except Exception as e:
            logger.error(f"Error updating relationship: {e}")
            return MutationResult(success=False, message=str(e))
