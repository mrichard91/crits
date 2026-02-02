"""
Backdoor queries for CRITs GraphQL API.
"""

import logging
from typing import Optional

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.backdoor import BackdoorType

logger = logging.getLogger(__name__)


@strawberry.type
class BackdoorQueries:
    """Backdoor-related queries."""

    @strawberry.field(description="Get a single backdoor by ID")
    @require_permission("Backdoor.read")
    def backdoor(self, info: Info, id: str) -> Optional[BackdoorType]:
        """Get a single backdoor by its ID."""
        from bson import ObjectId
        from crits.backdoors.backdoor import Backdoor

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            backdoor = Backdoor.objects(__raw__=query).first()

            if backdoor:
                return BackdoorType.from_model(backdoor)
            return None

        except Exception as e:
            logger.error(f"Error fetching backdoor {id}: {e}")
            return None

    @strawberry.field(description="List backdoors with optional filtering")
    @require_permission("Backdoor.read")
    def backdoors(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        name_contains: Optional[str] = None,
        status: Optional[str] = None,
        campaign: Optional[str] = None,
    ) -> list[BackdoorType]:
        """List backdoors with optional filtering."""
        from crits.backdoors.backdoor import Backdoor

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = Backdoor.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if name_contains:
                queryset = queryset.filter(name__icontains=name_contains)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by('-modified')
            backdoors = queryset.skip(offset).limit(limit)

            return [BackdoorType.from_model(b) for b in backdoors]

        except Exception as e:
            logger.error(f"Error listing backdoors: {e}")
            return []

    @strawberry.field(description="Count backdoors with optional filtering")
    @require_permission("Backdoor.read")
    def backdoors_count(
        self,
        info: Info,
        status: Optional[str] = None,
        campaign: Optional[str] = None,
    ) -> int:
        """Count backdoors matching the filters."""
        from crits.backdoors.backdoor import Backdoor

        ctx: GraphQLContext = info.context

        try:
            queryset = Backdoor.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting backdoors: {e}")
            return 0
