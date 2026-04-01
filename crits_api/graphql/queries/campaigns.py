"""
Campaign queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_permission
from crits_api.db.tlo_records import (
    build_contains_filter,
    count_tlo_records,
    distinct_tlo_values,
    get_tlo_record,
    list_tlo_records,
    to_model_namespace,
)
from crits_api.graphql.types.campaign import CampaignType

logger = logging.getLogger(__name__)


@strawberry.type
class CampaignQueries:
    """Campaign-related queries."""

    @strawberry.field(description="Get a single campaign by ID")
    @require_permission("Campaign.read")
    def campaign(self, info: Info, id: str) -> CampaignType | None:
        """Get a single campaign by its ID."""
        try:
            campaign = get_tlo_record("campaigns", id)
            if campaign:
                return CampaignType.from_model(to_model_namespace(campaign))
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
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[CampaignType]:
        """List campaigns with optional filtering."""
        limit = min(limit, 100)

        try:
            filters = {
                **build_contains_filter("name", name_contains),
                **({"active": active} if active else {}),
                **({"status": status} if status else {}),
            }
            campaigns = list_tlo_records(
                "campaigns",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "name": "name",
                    "active": "active",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [CampaignType.from_model(to_model_namespace(campaign)) for campaign in campaigns]

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
        try:
            filters = {
                **build_contains_filter("name", name_contains),
                **({"active": active} if active else {}),
                **({"status": status} if status else {}),
            }
            return count_tlo_records("campaigns", filters=filters)

        except Exception as e:
            logger.error(f"Error counting campaigns: {e}")
            return 0

    @strawberry.field(description="Get campaign names for autocomplete")
    @require_permission("Campaign.read")
    def campaign_names(self, info: Info) -> list[str]:
        """Get list of all campaign names."""
        try:
            return distinct_tlo_values("campaigns", "name")
        except Exception as e:
            logger.error(f"Error getting campaign names: {e}")
            return []
