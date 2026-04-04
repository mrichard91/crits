"""
Screenshot queries for CRITs GraphQL API.
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
from crits_api.graphql.types.screenshot import ScreenshotType

logger = logging.getLogger(__name__)


@strawberry.type
class ScreenshotQueries:
    """Screenshot-related queries."""

    @strawberry.field(description="Get a single screenshot by ID")
    @require_permission("Screenshot.read")
    def screenshot(self, info: Info, id: str) -> ScreenshotType | None:
        """Get a single screenshot by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            screenshot = get_tlo_record("screenshots", id, filters=source_filter)
            if screenshot:
                return ScreenshotType.from_model(to_model_namespace(screenshot))
            return None

        except Exception as e:
            logger.error(f"Error fetching screenshot {id}: {e}")
            return None

    @strawberry.field(description="List screenshots with optional filtering")
    @require_permission("Screenshot.read")
    def screenshots(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        filename_contains: str | None = None,
        tag: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[ScreenshotType]:
        """List screenshots with optional filtering."""
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("filename", filename_contains),
                {"tags": tag} if tag else {},
            )

            screenshots = list_tlo_records(
                "screenshots",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "filename": "filename",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [
                ScreenshotType.from_model(to_model_namespace(screenshot))
                for screenshot in screenshots
            ]

        except Exception as e:
            logger.error(f"Error listing screenshots: {e}")
            return []

    @strawberry.field(description="Count screenshots with optional filtering")
    @require_permission("Screenshot.read")
    def screenshots_count(
        self,
        info: Info,
        filename_contains: str | None = None,
        tag: str | None = None,
    ) -> int:
        """Count screenshots matching the filters."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("filename", filename_contains),
                {"tags": tag} if tag else {},
            )

            return count_tlo_records("screenshots", filters=filters)

        except Exception as e:
            logger.error(f"Error counting screenshots: {e}")
            return 0
