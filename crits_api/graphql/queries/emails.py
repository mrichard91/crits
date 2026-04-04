"""
Email queries for CRITs GraphQL API.
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
from crits_api.graphql.types.email_type import EmailType

logger = logging.getLogger(__name__)


@strawberry.type
class EmailQueries:
    """Email-related queries."""

    @strawberry.field(description="Get a single email by ID")
    @require_permission("Email.read")
    def email(self, info: Info, id: str) -> EmailType | None:
        """Get a single email by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            email = get_tlo_record("emails", id, filters=source_filter)
            if email:
                return EmailType.from_model(to_model_namespace(email))
            return None

        except Exception as e:
            logger.error(f"Error fetching email {id}: {e}")
            return None

    @strawberry.field(description="List emails with optional filtering")
    @require_permission("Email.read")
    def emails(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        subject_contains: str | None = None,
        from_address: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[EmailType]:
        """List emails with optional filtering."""
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("subject", subject_contains),
                build_contains_filter("from_address", from_address),
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            emails = list_tlo_records(
                "emails",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "subject": "subject",
                    "fromAddress": "from_address",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [EmailType.from_model(to_model_namespace(email)) for email in emails]

        except Exception as e:
            logger.error(f"Error listing emails: {e}")
            return []

    @strawberry.field(description="Count emails with optional filtering")
    @require_permission("Email.read")
    def emails_count(
        self,
        info: Info,
        subject_contains: str | None = None,
        from_address: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count emails matching the filters."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("subject", subject_contains),
                build_contains_filter("from_address", from_address),
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            return count_tlo_records("emails", filters=filters)

        except Exception as e:
            logger.error(f"Error counting emails: {e}")
            return 0
