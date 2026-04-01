"""
Target queries for CRITs GraphQL API.
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
from crits_api.graphql.types.target import TargetType

logger = logging.getLogger(__name__)


@strawberry.type
class TargetQueries:
    """Target-related queries."""

    @strawberry.field(description="Get a single target by ID")
    @require_permission("Target.read")
    def target(self, info: Info, id: str) -> TargetType | None:
        """Get a single target by its ID."""
        try:
            target = get_tlo_record("targets", id)
            if target:
                return TargetType.from_model(to_model_namespace(target))
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
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[TargetType]:
        """List targets with optional filtering."""
        limit = min(limit, 100)

        try:
            filters = {
                **build_contains_filter("email_address", email_contains),
                **build_contains_filter("department", department),
                **build_contains_filter("division", division),
                **({"status": status} if status else {}),
                **({"campaign.name": campaign} if campaign else {}),
            }
            targets = list_tlo_records(
                "targets",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "emailAddress": "email_address",
                    "department": "department",
                    "division": "division",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [TargetType.from_model(to_model_namespace(target)) for target in targets]

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
        try:
            filters = {
                **build_contains_filter("email_address", email_contains),
                **build_contains_filter("department", department),
                **build_contains_filter("division", division),
                **({"status": status} if status else {}),
                **({"campaign.name": campaign} if campaign else {}),
            }
            return count_tlo_records("targets", filters=filters)

        except Exception as e:
            logger.error(f"Error counting targets: {e}")
            return 0

    @strawberry.field(description="Get distinct departments")
    @require_permission("Target.read")
    def target_departments(self, info: Info) -> list[str]:
        """Get list of distinct departments."""
        try:
            return distinct_tlo_values("targets", "department")
        except Exception as e:
            logger.error(f"Error getting departments: {e}")
            return []

    @strawberry.field(description="Get distinct divisions")
    @require_permission("Target.read")
    def target_divisions(self, info: Info) -> list[str]:
        """Get list of distinct divisions."""
        try:
            return distinct_tlo_values("targets", "division")
        except Exception as e:
            logger.error(f"Error getting divisions: {e}")
            return []
