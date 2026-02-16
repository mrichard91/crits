"""Direct Redis session management for CRITs GraphQL API.

Replaces Django's SessionStore with direct Redis operations for
creating and deleting sessions. Sessions are stored in a format
compatible with Django's cache-backed session backend so the
Django web service can still read them.
"""

import json
import logging
import secrets

import redis as sync_redis

logger = logging.getLogger(__name__)

# Django cache session key format: ":1:django.contrib.sessions.cache{key}"
_KEY_PREFIX = ":1:django.contrib.sessions.cache"


def create_session(redis_url: str, user_id: str, ttl: int) -> str:
    """Create a new session in Redis.

    Args:
        redis_url: Redis connection URL (e.g. redis://redis:6379/0)
        user_id: The user ID to store in the session
        ttl: Session time-to-live in seconds

    Returns:
        The 32-character hex session key
    """
    session_key = secrets.token_hex(16)  # 32-char hex string
    cache_key = f"{_KEY_PREFIX}{session_key}"
    session_data = json.dumps({"_auth_user_id": user_id})

    client = sync_redis.from_url(redis_url)
    try:
        client.setex(cache_key, ttl, session_data)
        logger.debug("Created session %s... (TTL=%ds)", session_key[:8], ttl)
    finally:
        client.close()

    return session_key


def delete_session(redis_url: str, session_key: str) -> None:
    """Delete a session from Redis.

    Tries all known key prefixes to ensure deletion regardless of
    which format was used to store the session.

    Args:
        redis_url: Redis connection URL
        session_key: The session key to delete
    """
    possible_keys = [
        f"{_KEY_PREFIX}{session_key}",
        f"django.contrib.sessions.cache{session_key}",
        session_key,
    ]

    client = sync_redis.from_url(redis_url)
    try:
        for key in possible_keys:
            client.delete(key)
        logger.debug("Deleted session %s...", session_key[:8])
    finally:
        client.close()
