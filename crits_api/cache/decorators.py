"""
Caching decorators for GraphQL resolvers.

Provides @cached for query caching and @invalidates for mutation cache invalidation.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.cache.keys import make_cache_key
from crits_api.cache.redis_client import cache
from crits_api.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


def cached(
    prefix: str,
    ttl: int | None = None,
    include_args: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to cache GraphQL resolver results.

    Cache keys include the user's source access hash to prevent
    permission leaks across users.

    Usage:
        @strawberry.field
        @cached("domain", ttl=900)
        async def domain(self, info: Info, id: str) -> Domain:
            ...

    Args:
        prefix: Cache key prefix (e.g., "domain", "sample_list")
        ttl: TTL in seconds (default: 15 minutes from settings)
        include_args: Include resolver args in cache key

    Returns:
        Decorated resolver function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if not settings.cache_enabled:
                return await func(*args, **kwargs)  # type: ignore[misc]

            # Extract info and context
            info: Info | None = None
            for arg in args:
                if isinstance(arg, Info):
                    info = arg
                    break
            if info is None:
                info = kwargs.get("info")

            # Build cache key
            ctx: GraphQLContext | None = None
            sources_hash = "anon"
            if info:
                ctx = info.context
                if ctx is not None and ctx.is_authenticated:
                    sources_hash = ctx.sources_hash

            # Build key args (exclude 'self' and 'info')
            key_kwargs = {}
            if include_args:
                key_kwargs = {k: v for k, v in kwargs.items() if k not in ("self", "info")}

            cache_key = make_cache_key(
                prefix,
                user_sources_hash=sources_hash,
                **key_kwargs,
            )

            # Try cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute resolver
            result = await func(*args, **kwargs)  # type: ignore[misc]

            # Cache result (convert to dict if needed for serialization)
            cacheable = result
            if hasattr(result, "__dict__"):
                # Strawberry types can be converted
                cacheable = _to_cacheable(result)

            await cache.set(cache_key, cacheable, ttl=ttl)

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def invalidates(*type_names: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to invalidate cache after a mutation.

    Usage:
        @strawberry.mutation
        @invalidates("domain", "domain_list")
        async def create_domain(self, info: Info, input: CreateDomainInput) -> Domain:
            ...

    Args:
        *type_names: Type names to invalidate (e.g., "domain", "sample")

    Returns:
        Decorated mutation function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Execute mutation first
            result = await func(*args, **kwargs)  # type: ignore[misc]

            # Invalidate caches
            for type_name in type_names:
                await cache.invalidate_type(type_name)

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def invalidates_object(
    type_name: str,
    id_param: str = "id",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to invalidate cache for a specific object after mutation.

    Usage:
        @strawberry.mutation
        @invalidates_object("domain", id_param="id")
        async def update_domain(self, info: Info, id: str, input: UpdateDomainInput) -> Domain:
            ...

    Args:
        type_name: Type name to invalidate
        id_param: Name of the ID parameter in the mutation

    Returns:
        Decorated mutation function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Execute mutation first
            result = await func(*args, **kwargs)  # type: ignore[misc]

            # Get object ID from kwargs
            object_id = kwargs.get(id_param)
            if object_id:
                await cache.invalidate_object(type_name, str(object_id))

            return result

        return wrapper  # type: ignore[return-value]

    return decorator


def invalidates_sync(*type_names: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Sync-compatible decorator to invalidate cache after a mutation.

    For use with sync resolvers (Strawberry runs them in a thread pool).
    Fires cache invalidation as a background async task.

    Usage:
        @strawberry.mutation
        @invalidates_sync("domain")
        def create_domain(self, info: Info, ...) -> MutationResult:
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            result = func(*args, **kwargs)

            if settings.cache_enabled:
                _fire_invalidation(type_names)

            return result

        return wrapper

    return decorator


def invalidates_object_sync(
    type_name: str,
    id_param: str = "id",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Sync-compatible decorator to invalidate cache for a specific object.

    Usage:
        @strawberry.mutation
        @invalidates_object_sync("domain")
        def update_domain(self, info: Info, id: str, ...) -> MutationResult:
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            result = func(*args, **kwargs)

            if settings.cache_enabled:
                object_id = kwargs.get(id_param)
                if object_id:
                    _fire_object_invalidation(type_name, str(object_id))
                else:
                    _fire_invalidation((type_name,))

            return result

        return wrapper

    return decorator


def _fire_invalidation(type_names: tuple[str, ...]) -> None:
    """Fire-and-forget async cache invalidation from a sync context."""
    import asyncio

    async def _do_invalidate() -> None:
        for type_name in type_names:
            await cache.invalidate_type(type_name)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_do_invalidate())
    except RuntimeError:
        # No running loop - run synchronously
        asyncio.run(_do_invalidate())


def _fire_object_invalidation(type_name: str, object_id: str) -> None:
    """Fire-and-forget async cache invalidation for a specific object."""
    import asyncio

    async def _do_invalidate() -> None:
        await cache.invalidate_object(type_name, object_id)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_do_invalidate())
    except RuntimeError:
        asyncio.run(_do_invalidate())


def _to_cacheable(obj: Any) -> Any:
    """
    Convert an object to a cacheable format.

    Handles Strawberry types, dataclasses, and Pydantic models.
    """
    if obj is None:
        return None

    if isinstance(obj, str | int | float | bool):
        return obj

    if isinstance(obj, list | tuple):
        return [_to_cacheable(item) for item in obj]

    if isinstance(obj, dict):
        return {k: _to_cacheable(v) for k, v in obj.items()}

    if hasattr(obj, "model_dump"):
        # Pydantic model
        return obj.model_dump()

    if hasattr(obj, "__dataclass_fields__"):
        # Dataclass (including Strawberry types)
        return {k: _to_cacheable(getattr(obj, k)) for k in obj.__dataclass_fields__}

    if hasattr(obj, "__dict__"):
        return {k: _to_cacheable(v) for k, v in obj.__dict__.items()}

    # Fallback
    return str(obj)
