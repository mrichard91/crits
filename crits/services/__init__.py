"""Lazy accessors for the legacy service manager."""

from __future__ import annotations

from typing import Any

_manager = None


def _build_manager():
    """Import and construct the legacy service manager on demand."""
    from crits.services.core import ServiceManager

    return ServiceManager()


def get_service_manager():
    """Return the cached service manager, creating it on first use."""
    global _manager
    if _manager is None:
        _manager = _build_manager()
    return _manager


def reset_service_manager():
    """Clear the cached service manager."""
    global _manager
    _manager = None


class _ServiceManagerProxy:
    """Preserve the legacy ``crits.services.manager`` access pattern lazily."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_service_manager(), name)


manager = _ServiceManagerProxy()

__all__ = ["get_service_manager", "manager", "reset_service_manager"]
