"""
PCAP queries for CRITs GraphQL API.
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
    get_tlo_record,
    list_tlo_records,
    to_model_namespace,
)
from crits_api.graphql.types.pcap import PCAPType

logger = logging.getLogger(__name__)


@strawberry.type
class PCAPQueries:
    """PCAP-related queries."""

    @strawberry.field(description="Get a single PCAP by ID")
    @require_permission("PCAP.read")
    def pcap(self, info: Info, id: str) -> PCAPType | None:
        """Get a single PCAP by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            pcap = get_tlo_record("pcaps", id, filters=source_filter)
            if pcap:
                return PCAPType.from_model(to_model_namespace(pcap))
            return None

        except Exception as e:
            logger.error(f"Error fetching PCAP {id}: {e}")
            return None

    @strawberry.field(description="List PCAPs with optional filtering")
    @require_permission("PCAP.read")
    def pcaps(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        filename_contains: str | None = None,
        md5: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[PCAPType]:
        """List PCAPs with optional filtering."""
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("filename", filename_contains),
                {"md5": md5} if md5 else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            pcaps = list_tlo_records(
                "pcaps",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "filename": "filename",
                    "md5": "md5",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [PCAPType.from_model(to_model_namespace(pcap)) for pcap in pcaps]

        except Exception as e:
            logger.error(f"Error listing PCAPs: {e}")
            return []

    @strawberry.field(description="Count PCAPs with optional filtering")
    @require_permission("PCAP.read")
    def pcaps_count(
        self,
        info: Info,
        filename_contains: str | None = None,
        md5: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count PCAPs matching the filters."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("filename", filename_contains),
                {"md5": md5} if md5 else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            return count_tlo_records("pcaps", filters=filters)

        except Exception as e:
            logger.error(f"Error counting PCAPs: {e}")
            return 0
