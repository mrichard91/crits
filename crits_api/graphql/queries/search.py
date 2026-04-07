"""Global search query across all TLO types."""

import logging
from datetime import datetime

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.db.tlo_lookup import (
    display_value_for_record,
    iter_tlo_lookup_configs,
    search_tlo_records,
)

logger = logging.getLogger(__name__)


@strawberry.type
class SearchResult:
    """A single search result from cross-TLO search."""

    id: str
    tlo_type: str
    display_value: str
    modified: datetime | None = None
    status: str = ""


@strawberry.type
class SearchQueries:
    """Global search queries."""

    @strawberry.field(description="Search across all TLO types")
    @require_authenticated
    def search(
        self,
        info: Info,
        query: str,
        types: list[str] | None = None,
        limit: int = 25,
    ) -> list[SearchResult]:
        """
        Search across all (or specified) TLO types.

        Args:
            query: Search string (case-insensitive contains match)
            types: Optional list of TLO type names to search (e.g., ["Indicator", "Domain"])
            limit: Maximum total results (default 25, max 100)

        Returns:
            List of SearchResult sorted by modified date descending
        """
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        if not query or len(query) < 2:
            return []

        results: list[SearchResult] = []
        search_types = list(iter_tlo_lookup_configs(types))
        per_type_limit = max(5, limit // max(len(search_types), 1))

        for tlo_type, _config in search_types:
            try:
                source_filter = {}
                if not ctx.is_superuser:
                    source_filter = ctx.get_source_filter()

                for record in search_tlo_records(
                    tlo_type,
                    query,
                    filters=source_filter,
                    limit=per_type_limit,
                ):
                    results.append(
                        SearchResult(
                            id=str(record.get("_id", "")),
                            tlo_type=tlo_type,
                            display_value=display_value_for_record(record, tlo_type),
                            modified=record.get("modified"),
                            status=str(record.get("status", "") or ""),
                        )
                    )
            except Exception as e:
                logger.error("Error searching %s: %s", tlo_type, e)

        # Sort all results by modified descending, then trim to limit
        results.sort(key=lambda r: r.modified or datetime.min, reverse=True)
        return results[:limit]
