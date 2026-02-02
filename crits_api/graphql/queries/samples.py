"""
Sample queries for CRITs GraphQL API.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_permission
from crits_api.graphql.types.sample import SampleType

logger = logging.getLogger(__name__)


@strawberry.type
class SampleQueries:
    """Sample-related queries."""

    @strawberry.field(description="Get a single sample by ID")
    @require_permission("Sample.read")
    def sample(self, info: Info, id: str) -> SampleType | None:
        """Get a single sample by its ID."""
        from bson import ObjectId

        from crits.samples.sample import Sample

        ctx: GraphQLContext = info.context

        try:
            query = {"_id": ObjectId(id)}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            sample = Sample.objects(__raw__=query).first()

            if sample:
                return SampleType.from_model(sample)
            return None

        except Exception as e:
            logger.error(f"Error fetching sample {id}: {e}")
            return None

    @strawberry.field(description="Get a sample by MD5 hash")
    @require_permission("Sample.read")
    def sample_by_md5(self, info: Info, md5: str) -> SampleType | None:
        """Get a sample by its MD5 hash."""
        from crits.samples.sample import Sample

        ctx: GraphQLContext = info.context

        try:
            query = {"md5": md5.lower()}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            sample = Sample.objects(__raw__=query).first()

            if sample:
                return SampleType.from_model(sample)
            return None

        except Exception as e:
            logger.error(f"Error fetching sample by MD5 {md5}: {e}")
            return None

    @strawberry.field(description="Get a sample by SHA256 hash")
    @require_permission("Sample.read")
    def sample_by_sha256(self, info: Info, sha256: str) -> SampleType | None:
        """Get a sample by its SHA256 hash."""
        from crits.samples.sample import Sample

        ctx: GraphQLContext = info.context

        try:
            query = {"sha256": sha256.lower()}

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    query.update(source_filter)

            sample = Sample.objects(__raw__=query).first()

            if sample:
                return SampleType.from_model(sample)
            return None

        except Exception as e:
            logger.error(f"Error fetching sample by SHA256 {sha256}: {e}")
            return None

    @strawberry.field(description="List samples with optional filtering")
    @require_permission("Sample.read")
    def samples(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        filename_contains: str | None = None,
        filetype: str | None = None,
        md5: str | None = None,
        sha256: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> list[SampleType]:
        """List samples with optional filtering."""
        from crits.samples.sample import Sample

        ctx: GraphQLContext = info.context
        limit = min(limit, 100)

        try:
            queryset = Sample.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if filename_contains:
                queryset = queryset.filter(filename__icontains=filename_contains)

            if filetype:
                queryset = queryset.filter(filetype__icontains=filetype)

            if md5:
                queryset = queryset.filter(md5=md5.lower())

            if sha256:
                queryset = queryset.filter(sha256=sha256.lower())

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            queryset = queryset.order_by("-modified")
            samples = queryset.skip(offset).limit(limit)

            return [SampleType.from_model(s) for s in samples]

        except Exception as e:
            logger.error(f"Error listing samples: {e}")
            return []

    @strawberry.field(description="Count samples with optional filtering")
    @require_permission("Sample.read")
    def samples_count(
        self,
        info: Info,
        filetype: str | None = None,
        status: str | None = None,
        campaign: str | None = None,
    ) -> int:
        """Count samples matching the filters."""
        from crits.samples.sample import Sample

        ctx: GraphQLContext = info.context

        try:
            queryset = Sample.objects

            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            if filetype:
                queryset = queryset.filter(filetype__icontains=filetype)

            if status:
                queryset = queryset.filter(status=status)

            if campaign:
                queryset = queryset.filter(campaign__name=campaign)

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting samples: {e}")
            return 0

    @strawberry.field(description="Get distinct sample file types")
    @require_permission("Sample.read")
    def sample_filetypes(self, info: Info) -> list[str]:
        """Get list of distinct sample file types."""
        from crits.samples.sample import Sample

        try:
            types = Sample.objects.distinct("filetype")
            return sorted([t for t in types if t])
        except Exception as e:
            logger.error(f"Error getting sample filetypes: {e}")
            return []
