"""
GraphQL context factory for CRITs API.

Creates a GraphQLContext for each request with user info and permissions.
"""

import logging

from fastapi import Request
from starlette.responses import Response

from crits_api.auth.context import GraphQLContext
from crits_api.auth.session import (
    get_user_from_session,
    load_user_acl,
    load_user_sources,
)

logger = logging.getLogger(__name__)


async def get_context(request: Request, response: Response) -> GraphQLContext:
    """
    Create GraphQL context for a request.

    Loads user from Django session and populates ACL/sources.

    Args:
        request: FastAPI request object
        response: FastAPI response object (for setting cookies in mutations)

    Returns:
        GraphQLContext with user info and permissions
    """
    # Try to get authenticated user from Django session
    user = await get_user_from_session(request)

    if user:
        # Load ACL and sources
        acl = load_user_acl(user)
        sources = load_user_sources(user)

        logger.debug(f"Created context for user {user.username} with {len(sources)} source(s)")

        return GraphQLContext(
            request=request,
            response=response,
            user=user,
            acl=acl,
            sources=sources,
        )

    # Anonymous user
    logger.debug("Created anonymous context")
    return GraphQLContext(request=request, response=response)
