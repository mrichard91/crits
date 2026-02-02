"""
Domain queries for CRITs GraphQL API.
"""

import logging
from typing import Optional

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.domain import DomainType

logger = logging.getLogger(__name__)


@strawberry.type
class DomainQueries:
    """Domain-related queries."""

    @strawberry.field(description="Get a single domain by ID")
    @require_permission("Domain.read")
    def domain(self, info: Info, id: str) -> Optional[DomainType]:
        """Get a single domain by its ID."""
        from bson import ObjectId
        from crits.domains.domain import Domain

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            domain = Domain.objects(__raw__=query).first()

            if domain:
                return DomainType.from_model(domain)
            return None

        except Exception as e:
            logger.error(f"Error fetching domain {id}: {e}")
            return None

    @strawberry.field(description="List domains with optional filtering")
    @require_permission("Domain.read")
    def domains(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        domain_contains: Optional[str] = None,
        record_type: Optional[str] = None,
        status: Optional[str] = None,
        campaign: Optional[str] = None,
    ) -> list[DomainType]:
        """List domains with optional filtering."""
        from crits.domains.domain import Domain

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = Domain.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if domain_contains:
                queryset = queryset.filter(domain__icontains=domain_contains)

            if record_type:
                queryset = queryset.filter(record_type=record_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by('-modified')
            domains = queryset.skip(offset).limit(limit)

            return [DomainType.from_model(d) for d in domains]

        except Exception as e:
            logger.error(f"Error listing domains: {e}")
            return []

    @strawberry.field(description="Count domains with optional filtering")
    @require_permission("Domain.read")
    def domains_count(
        self,
        info: Info,
        record_type: Optional[str] = None,
        status: Optional[str] = None,
        campaign: Optional[str] = None,
    ) -> int:
        """Count domains matching the filters."""
        from crits.domains.domain import Domain

        ctx: GraphQLContext = info.context

        try:
            queryset = Domain.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if record_type:
                queryset = queryset.filter(record_type=record_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting domains: {e}")
            return 0

    @strawberry.field(description="Get distinct domain record types")
    @require_permission("Domain.read")
    def domain_record_types(self, info: Info) -> list[str]:
        """Get list of distinct domain record types."""
        from crits.domains.domain import Domain

        try:
            types = Domain.objects.distinct('record_type')
            return sorted([t for t in types if t])
        except Exception as e:
            logger.error(f"Error getting domain record types: {e}")
            return []
