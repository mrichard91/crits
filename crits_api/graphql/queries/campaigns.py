"""
Campaign queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.campaign import CampaignType

logger = logging.getLogger(__name__)


@strawberry.type
class CampaignQueries:
    """Campaign-related queries."""

    @strawberry.field(description="Get a single campaign by ID")
    @require_permission("Campaign.read")
    def campaign(self, info: Info, id: str) -> CampaignType | None:
        """Get a single campaign by its ID."""
        from bson import ObjectId

        from crits.campaigns.campaign import Campaign

        try:
            query = {"_id": ObjectId(id)}
            # Campaigns don't have source filtering - they're visible to all authenticated users

            campaign = Campaign.objects(__raw__=query).first()

            if campaign:
                return CampaignType.from_model(campaign)
            return None

        except Exception as e:
            logger.error(f"Error fetching campaign {id}: {e}")
            return None

    @strawberry.field(description="List campaigns with optional filtering")
    @require_permission("Campaign.read")
    def campaigns(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        name_contains: str | None = None,
        active: str | None = None,
        status: str | None = None,
    ) -> list[CampaignType]:
        """List campaigns with optional filtering."""
        from crits.campaigns.campaign import Campaign

        limit = min(limit, 100)

        try:
            queryset = Campaign.objects

            if name_contains:
                queryset = queryset.filter(name__icontains=name_contains)

            if active:
                queryset = queryset.filter(active=active)

            if status:
                queryset = queryset.filter(status=status)

            queryset = queryset.order_by("-modified")
            campaigns = queryset.skip(offset).limit(limit)

            return [CampaignType.from_model(c) for c in campaigns]

        except Exception as e:
            logger.error(f"Error listing campaigns: {e}")
            return []

    @strawberry.field(description="Count campaigns with optional filtering")
    @require_permission("Campaign.read")
    def campaigns_count(
        self,
        info: Info,
        name_contains: str | None = None,
        active: str | None = None,
        status: str | None = None,
    ) -> int:
        """Count campaigns matching the filters."""
        from crits.campaigns.campaign import Campaign

        try:
            queryset = Campaign.objects

            if name_contains:
                queryset = queryset.filter(name__icontains=name_contains)

            if active:
                queryset = queryset.filter(active=active)

            if status:
                queryset = queryset.filter(status=status)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting campaigns: {e}")
            return 0

    @strawberry.field(description="Get campaign names for autocomplete")
    @require_permission("Campaign.read")
    def campaign_names(self, info: Info) -> list[str]:
        """Get list of all campaign names."""
        from crits.campaigns.campaign import Campaign

        try:
            names = Campaign.objects.distinct("name")
            return sorted([n for n in names if n])
        except Exception as e:
            logger.error(f"Error getting campaign names: {e}")
            return []
