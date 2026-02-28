"""Tag (bucket list) queries for CRITs GraphQL API."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.graphql.queries.relationships import TLO_TYPE_CONFIG, get_model_class
from crits_api.graphql.queries.search import SearchResult

logger = logging.getLogger(__name__)

BUCKET_TYPE_FIELDS = [
    "Actor",
    "Backdoor",
    "Campaign",
    "Certificate",
    "Domain",
    "Email",
    "Event",
    "Exploit",
    "Indicator",
    "IP",
    "PCAP",
    "RawData",
    "Sample",
    "Signature",
    "Target",
]


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
        from crits.core.bucket import Bucket

        results = []
        for b in Bucket.objects.order_by("name"):
            total = sum(getattr(b, t, 0) for t in BUCKET_TYPE_FIELDS)
            if total > 0:
                results.append(TagSummary(name=b.name, total=total))
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

        if tlo_type not in TLO_TYPE_CONFIG:
            logger.warning("Unknown TLO type for tagged_objects: %s", tlo_type)
            return []

        model_path, _search_field, display_field = TLO_TYPE_CONFIG[tlo_type]

        try:
            model_class = get_model_class(model_path)
            queryset = model_class.objects(bucket_list=tag)

            # Apply source/TLP filtering
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            queryset = queryset.order_by("-modified").skip(offset).limit(limit)

            results = []
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
            return results
        except Exception as e:
            logger.error("Error fetching tagged %s objects: %s", tlo_type, e)
            return []
