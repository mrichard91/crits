"""
Domain queries for CRITs GraphQL API.
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
    distinct_tlo_values,
    get_tlo_record,
    list_tlo_records,
    to_model_namespace,
)
from crits_api.db.tlo_vocabulary import DEFAULT_DOMAIN_RECORD_TYPES
from crits_api.graphql.types.domain import DomainType

logger = logging.getLogger(__name__)


@strawberry.type
class DomainQueries:
    """Domain-related queries."""

    @strawberry.field(description="Get a single domain by ID")
    @require_permission("Domain.read")
    def domain(self, info: Info, id: str) -> DomainType | None:
        """Get a single domain by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            domain = get_tlo_record("domains", id, filters=source_filter)
            if domain:
                return DomainType.from_model(to_model_namespace(domain))
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
        domain_contains: str | None = None,
        record_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> list[DomainType]:
        """List domains with optional filtering."""
        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("domain", domain_contains),
                {"record_type": record_type} if record_type else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            domains = list_tlo_records(
                "domains",
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_dir=sort_dir,
                allowed_sort_fields={
                    "domain": "domain",
                    "recordType": "record_type",
                    "status": "status",
                    "modified": "modified",
                    "created": "created",
                },
            )

            return [DomainType.from_model(to_model_namespace(domain)) for domain in domains]

        except Exception as e:
            logger.error(f"Error listing domains: {e}")
            return []

    @strawberry.field(description="Count domains with optional filtering")
    @require_permission("Domain.read")
    def domains_count(
        self,
        info: Info,
        domain_contains: str | None = None,
        record_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count domains matching the filters."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            filters = combine_filters(
                source_filter,
                build_contains_filter("domain", domain_contains),
                {"record_type": record_type} if record_type else {},
                {"status": status} if status else {},
                {"campaign.name": campaign} if campaign else {},
            )

            return count_tlo_records("domains", filters=filters)

        except Exception as e:
            logger.error(f"Error counting domains: {e}")
            return 0

    @strawberry.field(description="Get distinct domain record types")
    @require_permission("Domain.read")
    def domain_record_types(self, info: Info) -> list[str]:
        """Get list of distinct domain record types (common DNS types + any custom DB values)."""
        values = set(DEFAULT_DOMAIN_RECORD_TYPES)
        values.update(distinct_tlo_values("domains", "record_type"))
        return sorted(values)
