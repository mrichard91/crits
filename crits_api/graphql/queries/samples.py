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


def _read_sample_file(md5: str) -> bytes | None:
    """Read file data from GridFS via the Sample model's filedata field.

    The legacy get_file() looks up GridFS files by MD5, but MongoDB 7+
    no longer stores MD5 checksums in GridFS .files collection by default.
    This bypasses that by reading directly from the Sample model.
    """
    from crits.samples.sample import Sample

    try:
        sample = Sample.objects(md5=md5).first()
        if sample is None or sample.filedata.grid_id is None:
            return None
        return sample.filedata.read()
    except Exception as e:
        logger.error(f"Error reading file data for {md5}: {e}")
        return None


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
        filename_contains: str | None = None,
        filetype: str | None = None,
        md5: str | None = None,
        sha256: str | None = None,
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

            return queryset.count()

        except Exception as e:
            logger.error(f"Error counting samples: {e}")
            return 0

    @strawberry.field(description="Extract ASCII and Unicode strings from a sample")
    @require_permission("Sample.read")
    def sample_strings(self, info: Info, md5: str) -> str | None:
        """Extract strings from a sample by MD5."""
        try:
            from crits.core.data_tools import make_ascii_strings, make_unicode_strings

            raw = _read_sample_file(md5)
            if raw is None:
                return None
            # Decode bytes to str via latin-1 (preserves all byte values 0-255)
            # so legacy Python 2 string operations in data_tools work correctly.
            decoded = raw.decode("latin-1") if isinstance(raw, bytes) else raw

            ascii_strings = make_ascii_strings(data=decoded)
            unicode_strings = make_unicode_strings(data=decoded)
            parts = []
            if ascii_strings:
                parts.append("=== ASCII Strings ===\n" + ascii_strings)
            if unicode_strings:
                parts.append("=== Unicode Strings ===\n" + unicode_strings)
            return "\n\n".join(parts) if parts else None
        except Exception as e:
            logger.error(f"Error extracting strings for {md5}: {e}")
            return None

    @strawberry.field(description="Get hex dump of a sample")
    @require_permission("Sample.read")
    def sample_hex(self, info: Info, md5: str, length: int = 4096) -> str | None:
        """Get hex dump of a sample by MD5."""
        try:
            from crits.core.data_tools import make_hex

            raw = _read_sample_file(md5)
            if raw is None:
                return None
            decoded = raw.decode("latin-1") if isinstance(raw, bytes) else raw
            return make_hex(data=decoded[:length])
        except Exception as e:
            logger.error(f"Error getting hex for {md5}: {e}")
            return None

    @strawberry.field(description="XOR search across byte keys for a sample")
    @require_permission("Sample.read")
    def sample_xor_search(
        self,
        info: Info,
        md5: str,
        search_string: str | None = None,
        skip_nulls: int = 0,
    ) -> list[int]:
        """Search for XOR keys in a sample by MD5."""
        try:
            from crits.core.data_tools import xor_search

            raw = _read_sample_file(md5)
            if raw is None:
                return []
            decoded = raw.decode("latin-1") if isinstance(raw, bytes) else raw
            results = xor_search(data=decoded, string=search_string, skip_nulls=skip_nulls)
            if results is None:
                return []
            return list(results)
        except Exception as e:
            logger.error(f"Error in XOR search for {md5}: {e}")
            return []

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
