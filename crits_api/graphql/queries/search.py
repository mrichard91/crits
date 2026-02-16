"""Global search query across all TLO types."""

import logging
from datetime import datetime

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.graphql.queries.relationships import TLO_TYPE_CONFIG, get_model_class

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

        # Determine which types to search
        search_types = TLO_TYPE_CONFIG
        if types:
            search_types = {k: v for k, v in TLO_TYPE_CONFIG.items() if k in types}

        results: list[SearchResult] = []
        per_type_limit = max(5, limit // max(len(search_types), 1))

        for tlo_type, (model_path, search_field, display_field) in search_types.items():
            try:
                model_class = get_model_class(model_path)
                queryset = model_class.objects

                # Apply source/TLP filtering
                if not ctx.is_superuser:
                    source_filter = ctx.get_source_filter()
                    if source_filter:
                        queryset = queryset.filter(__raw__=source_filter)

                # Search with case-insensitive contains
                filter_kwargs = {f"{search_field}__icontains": query}
                queryset = queryset.filter(**filter_kwargs)
                queryset = queryset.order_by("-modified").limit(per_type_limit)

                for obj in queryset:
                    display = getattr(obj, display_field, None)
                    results.append(
                        SearchResult(
                            id=str(obj.id),
                            tlo_type=tlo_type,
                            display_value=str(display) if display else str(obj.id),
                            modified=getattr(obj, "modified", None),
                            status=getattr(obj, "status", "") or "",
                        )
                    )
            except Exception as e:
                logger.error("Error searching %s: %s", tlo_type, e)

        # Sort all results by modified descending, then trim to limit
        results.sort(key=lambda r: r.modified or datetime.min, reverse=True)
        return results[:limit]
