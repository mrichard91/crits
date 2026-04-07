"""Relationship queries for CRITs GraphQL API."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.db.tlo_lookup import (
    TLO_LOOKUP_CONFIG,
    display_value_for_record,
    search_tlo_records,
)
from crits_api.db.tlo_vocabulary import DEFAULT_RELATIONSHIP_TYPES

logger = logging.getLogger(__name__)


@strawberry.type
class TLOSearchResult:
    """Result from a TLO search."""

    id: str
    display_value: str
    tlo_type: str


@strawberry.type
class RelationshipQueries:
    """Relationship-related queries."""

    @strawberry.field(description="Get available relationship types")
    @require_authenticated
    def relationship_types(self, info: Info) -> list[str]:
        """
        Get list of available relationship type values.

        Returns:
            Sorted list of relationship type strings
        """
        try:
            return sorted(DEFAULT_RELATIONSHIP_TYPES)
        except Exception as e:
            logger.error(f"Error getting relationship types: {e}")
            return []

    @strawberry.field(description="Search for TLOs by type and value")
    @require_authenticated
    def search_tlos(
        self,
        info: Info,
        tlo_type: str,
        search_value: str,
        limit: int = 10,
    ) -> list[TLOSearchResult]:
        """
        Search for TLOs by type and display value.

        Args:
            tlo_type: The TLO type to search (e.g., "Indicator", "Domain")
            search_value: The value to search for (case-insensitive contains)
            limit: Maximum number of results (default 10, max 25)

        Returns:
            List of matching TLOs with id and display value
        """
        ctx: GraphQLContext = info.context
        limit = min(limit, 25)

        if tlo_type not in TLO_LOOKUP_CONFIG:
            logger.warning(f"Unknown TLO type: {tlo_type}")
            return []

        if not search_value or len(search_value) < 2:
            return []

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            matches = search_tlo_records(
                tlo_type,
                search_value,
                filters=source_filter,
                limit=limit,
            )

            results = []
            for record in matches:
                results.append(
                    TLOSearchResult(
                        id=str(record.get("_id", "")),
                        display_value=display_value_for_record(record, tlo_type),
                        tlo_type=tlo_type,
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Error searching {tlo_type}: {e}")
            return []
