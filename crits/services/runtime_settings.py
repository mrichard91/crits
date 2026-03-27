"""Raw config helpers for legacy service runtime settings."""

from __future__ import annotations

from functools import lru_cache
import os
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection


def _env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes"}


def _mongo_client_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "host": os.environ.get("MONGO_HOST", "localhost"),
        "port": int(os.environ.get("MONGO_PORT", 27017)),
    }

    username = os.environ.get("MONGO_USER", "")
    password = os.environ.get("MONGO_PASSWORD", "")
    replicaset = os.environ.get("MONGO_REPLICASET", "")

    if username:
        kwargs["username"] = username
    if password:
        kwargs["password"] = password
    if _env_bool("MONGO_SSL"):
        kwargs["ssl"] = True
    if replicaset:
        kwargs["replicaSet"] = replicaset

    return kwargs


@lru_cache(maxsize=1)
def _get_mongo_client() -> MongoClient[dict[str, Any]]:
    return MongoClient(**_mongo_client_kwargs())


def _get_config_collection() -> Collection[dict[str, Any]]:
    database_name = os.environ.get("MONGO_DATABASE", "crits")
    return _get_mongo_client()[database_name]["config"]


@lru_cache(maxsize=1)
def _get_runtime_config() -> dict[str, Any]:
    document = _get_config_collection().find_one({}) or {}
    return dict(document)


def get_company_name(default: str = "My Company") -> str:
    """Return the configured company name without importing Django settings."""

    value = _get_runtime_config().get("company_name", default)
    return str(value or default)


def get_service_dirs() -> tuple[str, ...]:
    """Return configured service discovery directories.

    Merge raw CRITs config with the SERVICE_DIRS environment variable,
    keeping env-provided entries first and de-duplicated.
    """

    service_dirs: list[str] = []

    env_dirs = os.environ.get("SERVICE_DIRS", "")
    if env_dirs:
        for path in env_dirs.split(":"):
            normalized = path.strip()
            if normalized and normalized not in service_dirs:
                service_dirs.append(normalized)

    value = _get_runtime_config().get("service_dirs", [])
    if isinstance(value, tuple):
        configured_paths = value
    elif isinstance(value, list):
        configured_paths = value
    else:
        configured_paths = []

    for path in configured_paths:
        normalized = str(path).strip()
        if normalized and normalized not in service_dirs:
            service_dirs.append(normalized)

    return tuple(service_dirs)
