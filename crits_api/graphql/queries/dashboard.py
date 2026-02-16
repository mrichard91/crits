"""Dashboard statistics query."""

import logging
from datetime import datetime

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.graphql.queries.relationships import TLO_TYPE_CONFIG, get_model_class

logger = logging.getLogger(__name__)


@strawberry.type
class TLOCount:
    """Count of objects for a TLO type."""

    tlo_type: str
    count: int


@strawberry.type
class RecentActivity:
    """A recently modified TLO."""

    id: str
    tlo_type: str
    display_value: str
    modified: datetime | None = None
    analyst: str = ""


@strawberry.type
class TopCampaign:
    """Campaign with associated TLO count."""

    name: str
    count: int


@strawberry.type
class DashboardStats:
    """Aggregated dashboard statistics."""

    total_count: int
    counts: list[TLOCount]
    recent_activity: list[RecentActivity]
    top_campaigns: list[TopCampaign]


@strawberry.type
class DashboardQueries:
    """Dashboard-related queries."""

    @strawberry.field(description="Get dashboard statistics")
    @require_authenticated
    def dashboard_stats(self, info: Info) -> DashboardStats:
        """
        Get aggregated dashboard statistics including TLO counts,
        recent activity, and top campaigns.
        """
        ctx: GraphQLContext = info.context

        counts: list[TLOCount] = []
        total = 0
        recent_items: list[RecentActivity] = []

        for tlo_type, (model_path, _search_field, display_field) in TLO_TYPE_CONFIG.items():
            try:
                model_class = get_model_class(model_path)
                queryset = model_class.objects

                # Apply source/TLP filtering
                if not ctx.is_superuser:
                    source_filter = ctx.get_source_filter()
                    if source_filter:
                        queryset = queryset.filter(__raw__=source_filter)

                count = queryset.count()
                counts.append(TLOCount(tlo_type=tlo_type, count=count))
                total += count

                # Get most recent item for this type
                if count > 0:
                    recent = queryset.order_by("-modified").limit(1).first()
                    if recent:
                        display = getattr(recent, display_field, None)
                        recent_items.append(
                            RecentActivity(
                                id=str(recent.id),
                                tlo_type=tlo_type,
                                display_value=str(display) if display else str(recent.id),
                                modified=getattr(recent, "modified", None),
                                analyst=getattr(recent, "analyst", "") or "",
                            )
                        )
            except Exception as e:
                logger.error("Error getting stats for %s: %s", tlo_type, e)
                counts.append(TLOCount(tlo_type=tlo_type, count=0))

        # Sort recent activity by modified descending
        recent_items.sort(key=lambda r: r.modified or datetime.min, reverse=True)

        # Get top campaigns
        top_campaigns = _get_top_campaigns(ctx, limit=10)

        return DashboardStats(
            total_count=total,
            counts=counts,
            recent_activity=recent_items[:20],
            top_campaigns=top_campaigns,
        )


def _get_top_campaigns(ctx: GraphQLContext, limit: int = 10) -> list[TopCampaign]:
    """Get top campaigns by number of associated TLOs."""
    try:
        from crits.campaigns.campaign import Campaign

        queryset = Campaign.objects
        if not ctx.is_superuser:
            source_filter = ctx.get_source_filter()
            if source_filter:
                queryset = queryset.filter(__raw__=source_filter)

        campaigns: list[TopCampaign] = []
        for campaign in queryset.order_by("-modified").limit(limit):
            name = getattr(campaign, "name", "") or ""
            # Count is based on the campaign's associated objects
            count = len(getattr(campaign, "objects", []) or [])
            if not count:
                # Fallback: count relationships
                rels = getattr(campaign, "relationships", []) or []
                count = len(rels)
            campaigns.append(TopCampaign(name=name, count=count))

        # Sort by count descending
        campaigns.sort(key=lambda c: c.count, reverse=True)
        return campaigns[:limit]
    except Exception as e:
        logger.error("Error getting top campaigns: %s", e)
        return []
