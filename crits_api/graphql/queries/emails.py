"""
Email queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.email_type import EmailType

logger = logging.getLogger(__name__)


@strawberry.type
class EmailQueries:
    """Email-related queries."""

    @strawberry.field(description="Get a single email by ID")
    @require_permission("Email.read")
    def email(self, info: Info, id: str) -> EmailType | None:
        """Get a single email by its ID."""
        from bson import ObjectId

        from crits.emails.email import Email

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            email = Email.objects(__raw__=query).first()

            if email:
                return EmailType.from_model(email)
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
    ) -> list[EmailType]:
        """List emails with optional filtering."""
        from crits.emails.email import Email

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = Email.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if subject_contains:
                queryset = queryset.filter(subject__icontains=subject_contains)

            if from_address:
                queryset = queryset.filter(from_address__icontains=from_address)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by("-modified")
            emails = queryset.skip(offset).limit(limit)

            return [EmailType.from_model(e) for e in emails]

        except Exception as e:
            logger.error(f"Error listing emails: {e}")
            return []

    @strawberry.field(description="Count emails with optional filtering")
    @require_permission("Email.read")
    def emails_count(
        self,
        info: Info,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count emails matching the filters."""
        from crits.emails.email import Email

        ctx: GraphQLContext = info.context

        try:
            queryset = Email.objects

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
            logger.error(f"Error counting emails: {e}")
            return 0
