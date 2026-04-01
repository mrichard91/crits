"""
GraphQL context factory for CRITs API.

Creates a GraphQLContext for each request with user info and permissions.
"""

import logging
from typing import Any

from fastapi import Request
from graphql import parse
from graphql.language import FieldNode, OperationDefinitionNode
from starlette.responses import Response

from crits_api.auth.context import GraphQLContext
from crits_api.auth.session import (
    get_user_from_session,
    load_user_acl,
    load_user_sources,
)
from crits_api.db.auth_records import get_auth_config
from crits_api.db.connection import ensure_connected

logger = logging.getLogger(__name__)

_AUTH_ONLY_FIELDS = frozenset({"login", "logout"})


def _selected_operation(
    payload: dict[str, Any],
) -> OperationDefinitionNode | None:
    """Return the single selected GraphQL operation from a JSON payload."""

    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        return None

    operation_name = payload.get("operationName")
    if operation_name is not None and not isinstance(operation_name, str):
        return None

    try:
        document = parse(query)
    except Exception:
        return None

    operations = [
        definition
        for definition in document.definitions
        if isinstance(definition, OperationDefinitionNode)
    ]
    if not operations:
        return None

    if operation_name:
        for operation in operations:
            if operation.name and operation.name.value == operation_name:
                return operation
        return None

    if len(operations) != 1:
        return None

    return operations[0]


def _is_auth_only_operation(operation: OperationDefinitionNode | None) -> bool:
    """Return True when the selected operation only uses raw-backed auth fields."""

    if operation is None:
        return False

    for selection in operation.selection_set.selections:
        if not isinstance(selection, FieldNode):
            return False
        if selection.name.value not in _AUTH_ONLY_FIELDS:
            return False

    return True


async def _should_bootstrap_legacy_stack(request: Request) -> bool:
    """Decide whether this request needs the Django/MongoEngine stack."""

    if get_auth_config().ldap_auth:
        return True

    if request.method.upper() != "POST":
        return True

    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type:
        return True

    try:
        payload = await request.json()
    except Exception:
        return True

    if not isinstance(payload, dict):
        return True

    operation = _selected_operation(payload)
    return not _is_auth_only_operation(operation)


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
    if await _should_bootstrap_legacy_stack(request):
        ensure_connected()

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
