"""Dashboard statistics query."""

import logging
from datetime import datetime

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.db.tlo_lookup import (
    association_count_for_campaign,
    count_tlo_records_by_type,
    display_value_for_record,
    get_campaign_top_records,
    get_recent_tlo_record,
    iter_tlo_lookup_configs,
)

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

        for tlo_type, _config in iter_tlo_lookup_configs():
            try:
                source_filter = {}
                if not ctx.is_superuser:
                    source_filter = ctx.get_source_filter()

                count = count_tlo_records_by_type(tlo_type, filters=source_filter)
                counts.append(TLOCount(tlo_type=tlo_type, count=count))
                total += count

                if count > 0:
                    recent = get_recent_tlo_record(tlo_type, filters=source_filter)
                    if recent:
                        recent_items.append(
                            RecentActivity(
                                id=str(recent.get("_id", "")),
                                tlo_type=tlo_type,
                                display_value=display_value_for_record(recent, tlo_type),
                                modified=recent.get("modified"),
                                analyst=str(recent.get("analyst", "") or ""),
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
        filters = {}
        if not ctx.is_superuser:
            source_filter = ctx.get_source_filter()
            if source_filter:
                filters = source_filter

        campaigns: list[TopCampaign] = []
        for campaign in get_campaign_top_records(filters=filters, limit=limit):
            name = str(campaign.get("name", "") or "")
            count = association_count_for_campaign(campaign)
            campaigns.append(TopCampaign(name=name, count=count))

        campaigns.sort(key=lambda c: c.count, reverse=True)
        return campaigns[:limit]
    except Exception as e:
        logger.error("Error getting top campaigns: %s", e)
        return []
