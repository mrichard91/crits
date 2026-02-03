"""
Signature queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.signature import SignatureType

logger = logging.getLogger(__name__)


@strawberry.type
class SignatureQueries:
    """Signature-related queries."""

    @strawberry.field(description="Get a single signature by ID")
    @require_permission("Signature.read")
    def signature(self, info: Info, id: str) -> SignatureType | None:
        """Get a single signature by its ID."""
        from bson import ObjectId

        from crits.signatures.signature import Signature

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            signature = Signature.objects(__raw__=query).first()

            if signature:
                return SignatureType.from_model(signature)
            return None

        except Exception as e:
            logger.error(f"Error fetching signature {id}: {e}")
            return None

    @strawberry.field(description="List signatures with optional filtering")
    @require_permission("Signature.read")
    def signatures(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        title_contains: str | None = None,
        data_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> list[SignatureType]:
        """List signatures with optional filtering."""
        from crits.signatures.signature import Signature

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = Signature.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if title_contains:
                queryset = queryset.filter(title__icontains=title_contains)

            if data_type:
                queryset = queryset.filter(data_type=data_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by("-modified")
            signatures = queryset.skip(offset).limit(limit)

            return [SignatureType.from_model(s) for s in signatures]

        except Exception as e:
            logger.error(f"Error listing signatures: {e}")
            return []

    @strawberry.field(description="Count signatures with optional filtering")
    @require_permission("Signature.read")
    def signatures_count(
        self,
        info: Info,
        title_contains: str | None = None,
        data_type: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count signatures matching the filters."""
        from crits.signatures.signature import Signature

        ctx: GraphQLContext = info.context

        try:
            queryset = Signature.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if title_contains:
                queryset = queryset.filter(title__icontains=title_contains)

            if data_type:
                queryset = queryset.filter(data_type=data_type)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting signatures: {e}")
            return 0

    @strawberry.field(description="Get distinct signature data types")
    @require_permission("Signature.read")
    def signature_data_types(self, info: Info) -> list[str]:
        """Get list of distinct signature data types."""
        from crits.signatures.signature import Signature

        try:
            types = Signature.objects.distinct("data_type")
            return sorted([t for t in types if t])
        except Exception as e:
            logger.error(f"Error getting signature data types: {e}")
            return []
