"""
Permission checking utilities for CRITs GraphQL API.

Provides decorators and functions to enforce the same permission
model as Django handlers.
"""

import functools
import logging
from typing import Any, Callable, Optional, TypeVar

from strawberry.types import Info

from crits_api.auth.context import GraphQLContext

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PermissionDenied(Exception):
    """Raised when a user lacks required permissions."""

    def __init__(self, permission: str, message: Optional[str] = None):
        self.permission = permission
        self.message = message or f"Permission denied: {permission}"
        super().__init__(self.message)


def get_context(info: Info) -> GraphQLContext:
    """Extract GraphQL context from resolver info."""
    return info.context


def require_permission(permission: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to require a specific permission for a resolver.

    Usage:
        @strawberry.field
        @require_permission("Sample.read")
        def sample(self, info: Info, id: str) -> Sample:
            ...

    Args:
        permission: Permission string like "Sample.read" or "api_interface"

    Raises:
        PermissionDenied: If user lacks the required permission
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Find the info argument
            info = None
            for arg in args:
                if isinstance(arg, Info):
                    info = arg
                    break
            if info is None:
                info = kwargs.get("info")

            if info is None:
                raise RuntimeError("Resolver must have 'info: Info' parameter")

            ctx: GraphQLContext = info.context

            # Check authentication
            if not ctx.is_authenticated:
                raise PermissionDenied(permission, "Authentication required")

            # Check permission
            if not ctx.has_permission(permission):
                logger.warning(
                    f"Permission denied for user {ctx.user.username}: {permission}"
                )
                raise PermissionDenied(permission)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_authenticated(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to require authentication (but no specific permission).

    Usage:
        @strawberry.field
        @require_authenticated
        def me(self, info: Info) -> User:
            ...
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        info = None
        for arg in args:
            if isinstance(arg, Info):
                info = arg
                break
        if info is None:
            info = kwargs.get("info")

        if info is None:
            raise RuntimeError("Resolver must have 'info: Info' parameter")

        ctx: GraphQLContext = info.context

        if not ctx.is_authenticated:
            raise PermissionDenied("authentication", "Authentication required")

        return func(*args, **kwargs)

    return wrapper


def check_source_access(
    ctx: GraphQLContext,
    obj: Any,
    write: bool = False,
) -> bool:
    """
    Check if user can access an object based on source/TLP permissions.

    This replicates the logic from CRITsUser.check_source_tlp().

    Args:
        ctx: GraphQL context with user info
        obj: Object with 'source' field containing source information
        write: If True, check write access; otherwise check read access

    Returns:
        True if user can access the object
    """
    if ctx.is_superuser:
        return True

    if not ctx.is_authenticated:
        return False

    # Use the user's check method
    if hasattr(ctx.user, "check_source_tlp"):
        return ctx.user.check_source_tlp(obj)

    # Fallback: manual check
    sources = getattr(obj, "source", [])
    if not sources:
        return True  # No sources means public

    for source in sources:
        source_name = source.name if hasattr(source, "name") else str(source)

        for user_source in ctx.sources:
            if user_source.name != source_name:
                continue

            # Check appropriate access level
            if write:
                if user_source.write:
                    return True
            else:
                if user_source.read:
                    return True

    return False


def filter_by_sources(
    ctx: GraphQLContext,
    queryset: Any,
) -> Any:
    """
    Apply source/TLP filtering to a MongoEngine queryset.

    Args:
        ctx: GraphQL context with user info
        queryset: MongoEngine queryset to filter

    Returns:
        Filtered queryset
    """
    if ctx.is_superuser:
        return queryset

    if not ctx.is_authenticated:
        return queryset.none()

    # Get the filter query
    filter_query = ctx.get_source_filter()

    if filter_query:
        return queryset.filter(__raw__=filter_query)

    return queryset


# Convenience decorators for common TLO operations
def require_read(tlo_type: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Require read permission for a TLO type."""
    return require_permission(f"{tlo_type}.read")


def require_write(tlo_type: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Require write permission for a TLO type."""
    return require_permission(f"{tlo_type}.write")


def require_delete(tlo_type: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Require delete permission for a TLO type."""
    return require_permission(f"{tlo_type}.delete")
