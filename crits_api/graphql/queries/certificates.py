"""
Certificate queries for CRITs GraphQL API.
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
from crits_api.graphql.types.certificate import CertificateType

logger = logging.getLogger(__name__)


@strawberry.type
class CertificateQueries:
    """Certificate-related queries."""

    @strawberry.field(description="Get a single certificate by ID")
    @require_permission("Certificate.read")
    def certificate(self, info: Info, id: str) -> CertificateType | None:
        """Get a single certificate by its ID."""
        ctx: GraphQLContext = info.context

        try:
            source_filter = {}
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()

            cert = get_tlo_record("certificates", id, filters=source_filter)
            if cert:
                return CertificateType.from_model(to_model_namespace(cert))
            return None

        except Exception as e:
            logger.error(f"Error fetching certificate {id}: {e}")
            return None

    @strawberry.field(description="List certificates with optional filtering")
    @require_permission("Certificate.read")
    def certificates(
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
    ) -> list[CertificateType]:
        """List certificates with optional filtering."""
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

            certs = list_tlo_records(
                "certificates",
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

            return [CertificateType.from_model(to_model_namespace(cert)) for cert in certs]

        except Exception as e:
            logger.error(f"Error listing certificates: {e}")
            return []

    @strawberry.field(description="Count certificates with optional filtering")
    @require_permission("Certificate.read")
    def certificates_count(
        self,
        info: Info,
        filename_contains: str | None = None,
        md5: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count certificates matching the filters."""
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

            return count_tlo_records("certificates", filters=filters)

        except Exception as e:
            logger.error(f"Error counting certificates: {e}")
            return 0
