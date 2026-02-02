"""
Certificate queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.certificate import CertificateType

logger = logging.getLogger(__name__)


@strawberry.type
class CertificateQueries:
    """Certificate-related queries."""

    @strawberry.field(description="Get a single certificate by ID")
    @require_permission("Certificate.read")
    def certificate(self, info: Info, id: str) -> CertificateType | None:
        """Get a single certificate by its ID."""
        from bson import ObjectId

        from crits.certificates.certificate import Certificate

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            cert = Certificate.objects(__raw__=query).first()

            if cert:
                return CertificateType.from_model(cert)
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
    ) -> list[CertificateType]:
        """List certificates with optional filtering."""
        from crits.certificates.certificate import Certificate

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = Certificate.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if filename_contains:
                queryset = queryset.filter(filename__icontains=filename_contains)

            if md5:
                queryset = queryset.filter(md5=md5)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by("-modified")
            certs = queryset.skip(offset).limit(limit)

            return [CertificateType.from_model(c) for c in certs]

        except Exception as e:
            logger.error(f"Error listing certificates: {e}")
            return []

    @strawberry.field(description="Count certificates with optional filtering")
    @require_permission("Certificate.read")
    def certificates_count(
        self,
        info: Info,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count certificates matching the filters."""
        from crits.certificates.certificate import Certificate

        ctx: GraphQLContext = info.context

        try:
            queryset = Certificate.objects

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
            logger.error(f"Error counting certificates: {e}")
            return 0
