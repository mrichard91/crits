"""Tag (bucket list) queries for CRITs GraphQL API."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.db.tlo_lookup import (
    BUCKET_TYPE_FIELDS,
    TLO_LOOKUP_CONFIG,
    display_value_for_record,
    list_bucket_summary_records,
    list_tagged_tlo_records,
)
from crits_api.graphql.queries.search import SearchResult

logger = logging.getLogger(__name__)


@strawberry.type
class TagSummary:
    """A tag with its total object count."""

    name: str
    total: int


@strawberry.type
class TagQueries:
    """Tag-related queries."""

    @strawberry.field(description="Get all tags with object counts")
    @require_authenticated
    def tag_summary(self, info: Info) -> list[TagSummary]:
        """Return all tags with total counts across all TLO types."""
        results = []
        for record in list_bucket_summary_records():
            total = sum(int(record.get(tlo_type, 0) or 0) for tlo_type in BUCKET_TYPE_FIELDS)
            if total > 0:
                results.append(TagSummary(name=str(record.get("name", "") or ""), total=total))
        return results

    @strawberry.field(description="Get objects tagged with a specific bucket list name")
    @require_authenticated
    def tagged_objects(
        self,
        info: Info,
        tag: str,
        tlo_type: str,
        limit: int = 25,
        offset: int = 0,
    ) -> list[SearchResult]:
        """
        Return objects of a given type that have a specific tag.

        Args:
            tag: The tag (bucket list) name to search for
            tlo_type: The TLO type to search (e.g., "Indicator", "Domain")
            limit: Maximum number of results (default 25, max 100)
            offset: Number of results to skip (default 0)
        """
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        if tlo_type not in TLO_LOOKUP_CONFIG:
            logger.warning("Unknown TLO type for tagged_objects: %s", tlo_type)
            return []

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            results = []
            for record in list_tagged_tlo_records(
                tlo_type,
                tag,
                filters=source_filter,
                limit=limit,
                offset=offset,
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
            return results
        except Exception as e:
            logger.error("Error fetching tagged %s objects: %s", tlo_type, e)
            return []
