"""
Signature queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.db.tlo_records import (
    build_contains_filter,
    combine_filters,
    count_tlo_records,
    distinct_tlo_values,
    get_tlo_record,
    list_tlo_records,
    to_model_namespace,
)
from crits_api.graphql.types.signature import SignatureType

logger = logging.getLogger(__name__)


@strawberry.type
class SignatureQueries:
    """Signature-related queries."""

    @strawberry.field(description="Get a single signature by ID")
    @require_permission("Signature.read")
    def signature(self, info: Info, id: str) -> SignatureType | None:
        """Get a single signature by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            signature = get_tlo_record("signatures", id, filters=source_filter)
            if signature:
                return SignatureType.from_model(to_model_namespace(signature))
            return None

        except Exception as e:
            logger.error(f"Error fetching signature {id}: {e}")
            return None

    @strawberry.field(description="List signatures with optional filtering")
    @require_permission("Signature.read")
    def signatures(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        title_contains: str | None = None,
        data_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[SignatureType]:
        """List signatures with optional filtering."""
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("title", title_contains),
                {"data_type": data_type} if data_type else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            signatures = list_tlo_records(
                "signatures",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "title": "title",
                    "dataType": "data_type",
                    "version": "version",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [
                SignatureType.from_model(to_model_namespace(signature)) for signature in signatures
            ]

        except Exception as e:
            logger.error(f"Error listing signatures: {e}")
            return []

    @strawberry.field(description="Count signatures with optional filtering")
    @require_permission("Signature.read")
    def signatures_count(
        self,
        info: Info,
        title_contains: str | None = None,
        data_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count signatures matching the filters."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("title", title_contains),
                {"data_type": data_type} if data_type else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            return count_tlo_records("signatures", filters=filters)

        except Exception as e:
            logger.error(f"Error counting signatures: {e}")
            return 0

    @strawberry.field(description="Get distinct signature data types")
    @require_permission("Signature.read")
    def signature_data_types(self, info: Info) -> list[str]:
        """Get list of distinct signature data types."""
        try:
            return distinct_tlo_values("signatures", "data_type")
        except Exception as e:
            logger.error(f"Error getting signature data types: {e}")
            return []
