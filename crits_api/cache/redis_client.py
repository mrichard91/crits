"""
Redis client for CRITs GraphQL API caching.

Provides async Redis access for caching query results
with configurable TTL (default 15 minutes).
"""

import json
import logging
from typing import Any

import redis.asyncio as redis

from crits_api.config import settings

logger = logging.getLogger(__name__)

# Global Redis client
_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get or create the Redis client."""
    global _client
    if _client is None:
        _client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _client


async def close_redis() -> None:
    """Close the Redis connection."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None


class CacheClient:
    """
    High-level cache client for GraphQL query results.

    Handles serialization/deserialization and TTL management.
    """

    def __init__(self, default_ttl: int | None = None):
        """
        Initialize cache client.

        Args:
            default_ttl: Default TTL in seconds (default: 15 minutes from settings)
        """
        self.default_ttl = default_ttl or settings.cache_default_ttl

    async def get(self, key: str) -> Any | None:
        """
        Get cached value.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not settings.cache_enabled:
            return None

        try:
            client = await get_redis()
            data = await client.get(key)
            if data:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(data)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set cached value.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: TTL in seconds (default: self.default_ttl)

        Returns:
            True if successful
        """
        if not settings.cache_enabled:
            return False

        try:
            client = await get_redis()
            data = json.dumps(value, default=str)
            await client.setex(key, ttl or self.default_ttl, data)
            logger.debug(f"Cache SET: {key} (TTL: {ttl or self.default_ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete cached value.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted
        """
        try:
            client = await get_redis()
            result = await client.delete(key)
            logger.debug(f"Cache DELETE: {key} (existed: {result > 0})")
            return result > 0
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Uses SCAN to avoid blocking on large keyspaces.

        Args:
            pattern: Redis pattern (e.g., "crits:graphql:domain:*")

        Returns:
            Number of keys deleted
        """
        try:
            client = await get_redis()
            deleted = 0

            # Use SCAN to iterate without blocking
            async for key in client.scan_iter(match=pattern, count=100):
                await client.delete(key)
                deleted += 1

            logger.info(f"Cache DELETE pattern '{pattern}': {deleted} keys")
            return deleted
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def invalidate_type(self, type_name: str) -> int:
        """
        Invalidate all cached data for a TLO type.

        Args:
            type_name: TLO type name (e.g., "domain", "sample")

        Returns:
            Number of keys deleted
        """
        pattern = f"crits:graphql:{type_name}:*"
        return await self.delete_pattern(pattern)

    async def invalidate_object(self, type_name: str, object_id: str) -> int:
        """
        Invalidate cached data for a specific object.

        Args:
            type_name: TLO type name
            object_id: MongoDB ObjectId as string

        Returns:
            Number of keys deleted
        """
        # Delete both object-specific and list caches
        patterns = [
            f"crits:graphql:{type_name}:{object_id}:*",
            f"crits:graphql:{type_name}_list:*",
        ]
        deleted = 0
        for pattern in patterns:
            deleted += await self.delete_pattern(pattern)
        return deleted


# Default cache client instance
cache = CacheClient()
