"""
Cache key generation for CRITs GraphQL API.

Keys include user's source access hash to prevent permission leaks
when caching query results.
"""

import hashlib
import json
from typing import Any, Optional


def make_cache_key(
    prefix: str,
    *args: Any,
    user_sources_hash: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Generate a cache key for GraphQL query results.

    Pattern: crits:graphql:{prefix}:{args_hash}:{sources_hash}

    Args:
        prefix: Key prefix (e.g., "domain", "sample_list")
        *args: Positional arguments to include in key
        user_sources_hash: Hash of user's source access (for permission isolation)
        **kwargs: Keyword arguments to include in key

    Returns:
        Cache key string
    """
    parts = ["crits", "graphql", prefix]

    # Add args hash if any
    if args or kwargs:
        key_data = {"args": args, "kwargs": kwargs}
        data_str = json.dumps(key_data, sort_keys=True, default=str)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()[:12]
        parts.append(data_hash)

    # Add sources hash for permission isolation
    if user_sources_hash:
        parts.append(user_sources_hash)
    else:
        parts.append("anon")

    return ":".join(parts)


def make_type_pattern(type_name: str) -> str:
    """
    Generate a pattern to match all cache keys for a type.

    Args:
        type_name: TLO type name (e.g., "domain", "sample")

    Returns:
        Pattern string for Redis SCAN
    """
    return f"crits:graphql:{type_name}:*"


def make_object_pattern(type_name: str, object_id: str) -> str:
    """
    Generate a pattern to match cache keys for a specific object.

    Args:
        type_name: TLO type name
        object_id: MongoDB ObjectId as string

    Returns:
        Pattern string for Redis SCAN
    """
    return f"crits:graphql:{type_name}:{object_id}:*"
