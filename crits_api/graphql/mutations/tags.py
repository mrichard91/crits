"""Tag (bucket list) mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.cache.decorators import _fire_invalidation
from crits_api.graphql.types.common import MutationResult

logger = logging.getLogger(__name__)

# Mapping of TLO type to cache key prefix (same as relationships.py)
_TYPE_CACHE_KEY = {
    "Indicator": "indicator",
    "Actor": "actor",
    "Backdoor": "backdoor",
    "Campaign": "campaign",
    "Certificate": "certificate",
    "Domain": "domain",
    "Email": "email",
    "Event": "event",
    "Exploit": "exploit",
    "IP": "ip",
    "PCAP": "pcap",
    "RawData": "raw_data",
    "Sample": "sample",
    "Screenshot": "screenshot",
    "Signature": "signature",
    "Target": "target",
}


@strawberry.type
class TagMutations:
    @strawberry.mutation(description="Update bucket list (tags) for a TLO")
    @require_authenticated
    def update_bucket_list(
        self, info: Info, tlo_type: str, tlo_id: str, tags: list[str]
    ) -> MutationResult:
        from crits.core.handlers import modify_bucket_list

        ctx: GraphQLContext = info.context
        analyst = ctx.user.username if ctx.user else "unknown"

        try:
            modify_bucket_list(tlo_type, tlo_id, tags, analyst)

            # Invalidate cache for this TLO type
            from crits_api.config import settings

            if settings.cache_enabled and tlo_type in _TYPE_CACHE_KEY:
                _fire_invalidation((_TYPE_CACHE_KEY[tlo_type],))

            return MutationResult(success=True, message="Tags updated")
        except Exception as e:
            logger.error(f"Error updating bucket list: {e}")
            return MutationResult(success=False, message=str(e))
