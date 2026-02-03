"""
Screenshot queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.screenshot import ScreenshotType

logger = logging.getLogger(__name__)


@strawberry.type
class ScreenshotQueries:
    """Screenshot-related queries."""

    @strawberry.field(description="Get a single screenshot by ID")
    @require_permission("Screenshot.read")
    def screenshot(self, info: Info, id: str) -> ScreenshotType | None:
        """Get a single screenshot by its ID."""
        from bson import ObjectId

        from crits.screenshots.screenshot import Screenshot

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            screenshot = Screenshot.objects(__raw__=query).first()

            if screenshot:
                return ScreenshotType.from_model(screenshot)
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
    ) -> list[ScreenshotType]:
        """List screenshots with optional filtering."""
        from crits.screenshots.screenshot import Screenshot

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = Screenshot.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if filename_contains:
                queryset = queryset.filter(filename__icontains=filename_contains)

            if tag:
                queryset = queryset.filter(tags=tag)

            queryset = queryset.order_by("-modified")
            screenshots = queryset.skip(offset).limit(limit)

            return [ScreenshotType.from_model(s) for s in screenshots]

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
        from crits.screenshots.screenshot import Screenshot

        ctx: GraphQLContext = info.context

        try:
            queryset = Screenshot.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if filename_contains:
                queryset = queryset.filter(filename__icontains=filename_contains)

            if tag:
                queryset = queryset.filter(tags=tag)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting screenshots: {e}")
            return 0
