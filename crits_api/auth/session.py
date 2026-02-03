"""
Django session integration for CRITs GraphQL API.

Reads Django session cookies to authenticate users, allowing
session sharing between Django and FastAPI services.
"""

import json
import logging
import pickle
from typing import TYPE_CHECKING, Optional

import redis.asyncio as redis
from fastapi import Request

from crits_api.config import settings

if TYPE_CHECKING:
    from crits.core.user import CRITsUser

logger = logging.getLogger(__name__)

# Redis client for session access (binary mode for pickle data)
_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client for session access."""
    global _redis_client
    if _redis_client is None:
        # Don't decode responses - session data may be pickled binary
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=False,
        )
    return _redis_client


async def get_session_data(session_key: str) -> dict | None:
    """
    Load session data from Redis (Django cache session backend).

    Supports both pickle and JSON serialization for compatibility
    with sessions created before/after JSONSerializer setting.

    Args:
        session_key: The session ID from the cookie

    Returns:
        Session data dict or None if session doesn't exist
    """
    try:
        client = await get_redis_client()

        # Django cache backend uses key format: ":1:django.contrib.sessions.cache{key}"
        # The ":1:" prefix is from Django's cache key versioning
        possible_keys = [
            f":1:django.contrib.sessions.cache{session_key}",
            f"django.contrib.sessions.cache{session_key}",
            session_key,
        ]

        for key in possible_keys:
            data = await client.get(key)
            if data:
                logger.debug(f"Found session with key pattern: {key[:40]}...")

                # Try pickle first (older sessions)
                try:
                    session_data = pickle.loads(data)
                    if isinstance(session_data, dict):
                        logger.debug("Session loaded via pickle")
                        return session_data
                except (pickle.UnpicklingError, TypeError, AttributeError):
                    pass

                # Try JSON (newer sessions with JSONSerializer)
                try:
                    session_data = json.loads(data)
                    if isinstance(session_data, dict):
                        logger.debug("Session loaded via JSON")
                        return session_data
                except (json.JSONDecodeError, TypeError):
                    pass

                logger.debug("Could not deserialize session data")

        logger.debug(f"No session found for key: {session_key[:20]}...")
        return None

    except Exception as e:
        logger.error(f"Error loading session from Redis: {e}")
        return None


async def get_user_from_session(request: Request) -> Optional["CRITsUser"]:
    """
    Get the authenticated user from Django session cookie.

    Reads the sessionid cookie, loads session from Redis,
    and retrieves the CRITsUser object.

    Args:
        request: FastAPI request object

    Returns:
        CRITsUser object or None if not authenticated
    """
    # Import CRITsUser - Django should already be set up via connect_mongodb()
    from crits.core.user import CRITsUser

    # Get session cookie
    session_key = request.cookies.get(settings.session_cookie_name)
    if not session_key:
        logger.debug("No session cookie found")
        return None

    logger.debug(f"Looking up session: {session_key[:20]}...")

    # Try to load from Redis directly
    session_data = await get_session_data(session_key)

    if session_data:
        # Get user ID from session
        user_id = session_data.get("_auth_user_id")
        logger.debug(f"Session contains user_id: {user_id}")
        if user_id:
            try:
                user = CRITsUser.objects(id=user_id).first()
                if user and user.is_active:
                    logger.debug(f"Authenticated user from session: {user.username}")
                    return user
                elif user:
                    logger.debug(f"User {user.username} is not active")
                else:
                    logger.debug(f"User with id {user_id} not found")
            except Exception as e:
                logger.error(f"Error loading user {user_id}: {e}")

    # Fallback: Try Django's session framework directly (sync)
    try:
        from django.contrib.sessions.backends.cache import SessionStore

        store = SessionStore(session_key=session_key)
        if store.exists(session_key):
            user_id = store.get("_auth_user_id")
            logger.debug(f"Django SessionStore found user_id: {user_id}")
            if user_id:
                user = CRITsUser.objects(id=user_id).first()
                if user and user.is_active:
                    logger.debug(f"Authenticated user via Django session: {user.username}")
                    return user
    except Exception as e:
        logger.debug(f"Django session fallback failed: {e}")

    logger.debug("No authenticated user found")
    return None


def load_user_acl(user: "CRITsUser") -> dict:
    """
    Load and cache user's merged ACL permissions.

    Args:
        user: CRITsUser object

    Returns:
        Merged ACL dictionary from all user's roles
    """
    try:
        # get_access_list() merges permissions from all roles
        return user.get_access_list()
    except Exception as e:
        logger.error(f"Error loading ACL for user {user.username}: {e}")
        return {}


def load_user_sources(user: "CRITsUser") -> list:
    """
    Load user's source access list.

    Args:
        user: CRITsUser object

    Returns:
        List of SourceAccess objects
    """
    from crits_api.auth.context import SourceAccess

    sources = []
    try:
        acl = user.get_access_list()
        source_access_list = acl.get("sources", [])

        for source in source_access_list:
            sources.append(
                SourceAccess(
                    name=source.name,
                    read=getattr(source, "read", False),
                    write=getattr(source, "write", False),
                    tlp_red=getattr(source, "tlp_red", False),
                    tlp_amber=getattr(source, "tlp_amber", False),
                    tlp_green=getattr(source, "tlp_green", False),
                )
            )
    except Exception as e:
        logger.error(f"Error loading sources for user {user.username}: {e}")

    return sources
