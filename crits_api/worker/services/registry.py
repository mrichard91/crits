"""Service registry — @register_service decorator and lookup helpers."""

import importlib
import logging
import os
import sys
from typing import Any

from crits_api.worker.services.base import AnalysisService

logger = logging.getLogger(__name__)

# Global registry: service name -> service class
_registry: dict[str, type[AnalysisService]] = {}


def register_service(cls: type[AnalysisService]) -> type[AnalysisService]:
    """Class decorator that registers an AnalysisService subclass.

    Usage::

        @register_service
        class FileTypeService(AnalysisService):
            name = "filetype"
            ...
    """
    if not cls.name:
        raise ValueError(f"Service class {cls.__name__} must define a 'name' attribute")
    if cls.name in _registry:
        logger.warning("Overwriting service registration for '%s'", cls.name)
    _registry[cls.name] = cls
    logger.info("Registered service: %s v%s", cls.name, cls.version)
    return cls


def get_service(name: str) -> type[AnalysisService] | None:
    """Look up a registered modern service by name."""
    return _registry.get(name)


def get_all_services() -> dict[str, type[AnalysisService]]:
    """Return a copy of the full service registry."""
    return dict(_registry)


def get_triage_services() -> list[type[AnalysisService]]:
    """Return modern services marked run_on_triage=True, merged with legacy triage services.

    Modern services are returned first, then legacy services not already covered.
    """
    modern_triage = [cls for cls in _registry.values() if cls.run_on_triage]

    # Merge with legacy triage services from the DB
    legacy_names: list[str] = []
    try:
        from crits.services.handlers import triage_services as legacy_triage_services

        legacy_names = legacy_triage_services(status=True)
    except Exception:
        logger.debug("Could not load legacy triage services")

    # Filter out legacy services that have a modern replacement
    modern_names = {cls.name for cls in modern_triage}
    _legacy_only = [n for n in legacy_names if n not in modern_names]
    if _legacy_only:
        logger.debug("Legacy-only triage services: %s", _legacy_only)

    return modern_triage


def get_triage_service_names() -> list[str]:
    """Return names of all triage services (modern + legacy)."""
    modern = [cls.name for cls in _registry.values() if cls.run_on_triage]

    try:
        from crits.services.handlers import triage_services as legacy_triage_services

        legacy = legacy_triage_services(status=True)
    except Exception:
        legacy = []

    # Merge — modern first, then legacy not already covered
    seen = set(modern)
    combined = list(modern)
    for name in legacy:
        if name not in seen:
            combined.append(name)
            seen.add(name)
    return combined


def _discover_external_services() -> None:
    """Scan SERVICE_DIRS for external AnalysisService packages.

    Reads directories from both Django settings (MongoDB config) and the
    SERVICE_DIRS environment variable (colon-separated). For each directory,
    walks subdirectories looking for packages with ``__init__.py`` and imports
    them — the ``@register_service`` decorator fires on import.
    """
    service_dirs: list[str] = []

    # Source 1: Django settings (loaded from MongoDB config)
    try:
        from django.conf import settings

        service_dirs.extend(getattr(settings, "SERVICE_DIRS", ()))
    except Exception:
        pass

    # Source 2: SERVICE_DIRS env var (colon-separated paths)
    env_dirs = os.environ.get("SERVICE_DIRS", "")
    if env_dirs:
        for d in env_dirs.split(":"):
            d = d.strip()
            if d and d not in service_dirs:
                service_dirs.append(d)

    if not service_dirs:
        return

    for service_dir in service_dirs:
        if not os.path.isdir(service_dir):
            logger.warning("SERVICE_DIRS entry not found: %s", service_dir)
            continue

        # Add to sys.path so imports resolve
        if service_dir not in sys.path:
            sys.path.insert(0, service_dir)

        for entry in sorted(os.listdir(service_dir)):
            pkg_path = os.path.join(service_dir, entry)
            if not os.path.isdir(pkg_path):
                continue
            if not os.path.isfile(os.path.join(pkg_path, "__init__.py")):
                continue
            try:
                importlib.import_module(entry)
                logger.info("Loaded external service package: %s", entry)
            except Exception:
                logger.warning(
                    "Failed to import service package: %s",
                    entry,
                    exc_info=True,
                )


_registered = False


def ensure_services_registered() -> None:
    """Ensure built-in and external services are imported and registered.

    Safe to call multiple times; guarded by a module-level flag.
    """
    global _registered
    if _registered:
        return
    try:
        import crits_api.worker.services.builtin  # noqa: F401
    except ImportError:
        logger.debug("Built-in services not available")
    _discover_external_services()
    _registered = True


def list_all_service_info() -> list[dict[str, Any]]:
    """Return info dicts for all registered modern services."""
    ensure_services_registered()
    return [
        {
            "name": cls.name,
            "version": cls.version,
            "description": cls.description,
            "supported_types": cls.supported_types,
            "run_on_triage": cls.run_on_triage,
        }
        for cls in _registry.values()
    ]
