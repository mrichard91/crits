"""Service registry — @register_service decorator and lookup helpers."""

import importlib
import logging
import os
import sys
from typing import Any

from crits.services.runtime_settings import get_service_dirs
from crits_api.db.service_records import get_service_record, list_service_names
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


def _is_triage_enabled(cls: type[AnalysisService]) -> bool:
    """Check if a modern service should run on triage, respecting DB overrides."""
    try:
        db_record = get_service_record(cls.name)
        if db_record and db_record.run_on_triage is not None:
            return bool(db_record.run_on_triage)
    except Exception:
        logger.debug("Could not load triage override for %s", cls.name)
    return cls.run_on_triage


def _is_service_enabled(cls: type[AnalysisService]) -> bool:
    """Check if a modern service is enabled, respecting DB overrides."""
    try:
        db_record = get_service_record(cls.name)
        if db_record and db_record.enabled is not None:
            return bool(db_record.enabled)
    except Exception:
        logger.debug("Could not load enabled override for %s", cls.name)
    return True


def get_triage_services() -> list[type[AnalysisService]]:
    """Return modern services marked run_on_triage=True, merged with legacy triage services.

    Respects DB overrides for both the triage flag and the enabled flag.
    Modern services are returned first, then legacy services not already covered.
    """
    modern_triage = [
        cls for cls in _registry.values() if _is_triage_enabled(cls) and _is_service_enabled(cls)
    ]

    # Merge with legacy triage services from the DB
    try:
        legacy_names = list_service_names(
            {
                "run_on_triage": True,
                "enabled": True,
                "status": "available",
            }
        )
    except Exception:
        legacy_names = []
        logger.debug("Could not load legacy triage service names")

    # Filter out legacy services that have a modern replacement
    modern_names = {cls.name for cls in modern_triage}
    _legacy_only = [n for n in legacy_names if n not in modern_names]
    if _legacy_only:
        logger.debug("Legacy-only triage services: %s", _legacy_only)

    return modern_triage


def get_triage_service_names() -> list[str]:
    """Return names of all triage services (modern + legacy).

    Respects DB overrides for both the triage flag and the enabled flag.
    """
    modern = [
        cls.name
        for cls in _registry.values()
        if _is_triage_enabled(cls) and _is_service_enabled(cls)
    ]

    try:
        legacy = list_service_names(
            {
                "run_on_triage": True,
                "enabled": True,
                "status": "available",
            }
        )
    except Exception:
        legacy = []
        logger.debug("Could not load combined triage service names")

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

    Reads directories from raw CRITs config or the SERVICE_DIRS environment
    variable. For each directory, walks subdirectories looking for packages
    with ``__init__.py`` and imports them; the ``@register_service``
    decorator fires on import.
    """
    service_dirs = list(get_service_dirs())

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
