"""
Target queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.target import TargetType

logger = logging.getLogger(__name__)


@strawberry.type
class TargetQueries:
    """Target-related queries."""

    @strawberry.field(description="Get a single target by ID")
    @require_permission("Target.read")
    def target(self, info: Info, id: str) -> TargetType | None:
        """Get a single target by its ID."""
        from bson import ObjectId

        from crits.targets.target import Target

        try:
            query = {"_id": ObjectId(id)}

            target = Target.objects(__raw__=query).first()

            if target:
                return TargetType.from_model(target)
            return None

        except Exception as e:
            logger.error(f"Error fetching target {id}: {e}")
            return None

    @strawberry.field(description="List targets with optional filtering")
    @require_permission("Target.read")
    def targets(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        email_contains: str | None = None,
        department: str | None = None,
        division: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> list[TargetType]:
        """List targets with optional filtering."""
        from crits.targets.target import Target

        limit = min(limit, 100)

        try:
            queryset = Target.objects

            if email_contains:
                queryset = queryset.filter(email_address__icontains=email_contains)

            if department:
                queryset = queryset.filter(department__icontains=department)

            if division:
                queryset = queryset.filter(division__icontains=division)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by("-modified")
            targets = queryset.skip(offset).limit(limit)

            return [TargetType.from_model(t) for t in targets]

        except Exception as e:
            logger.error(f"Error listing targets: {e}")
            return []

    @strawberry.field(description="Count targets with optional filtering")
    @require_permission("Target.read")
    def targets_count(
        self,
        info: Info,
        email_contains: str | None = None,
        department: str | None = None,
        division: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count targets matching the filters."""
        from crits.targets.target import Target

        try:
            queryset = Target.objects

            if email_contains:
                queryset = queryset.filter(email_address__icontains=email_contains)

            if department:
                queryset = queryset.filter(department__icontains=department)

            if division:
                queryset = queryset.filter(division__icontains=division)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting targets: {e}")
            return 0

    @strawberry.field(description="Get distinct departments")
    @require_permission("Target.read")
    def target_departments(self, info: Info) -> list[str]:
        """Get list of distinct departments."""
        from crits.targets.target import Target

        try:
            depts = Target.objects.distinct("department")
            return sorted([d for d in depts if d])
        except Exception as e:
            logger.error(f"Error getting departments: {e}")
            return []

    @strawberry.field(description="Get distinct divisions")
    @require_permission("Target.read")
    def target_divisions(self, info: Info) -> list[str]:
        """Get list of distinct divisions."""
        from crits.targets.target import Target

        try:
            divs = Target.objects.distinct("division")
            return sorted([d for d in divs if d])
        except Exception as e:
            logger.error(f"Error getting divisions: {e}")
            return []
