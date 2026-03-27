"""Raw MongoDB access helpers for legacy service metadata records."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import os
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection

SERVICE_RECORD_SCHEMA_VERSION = 1


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


def _get_services_collection() -> Collection[dict[str, Any]]:
    database_name = os.environ.get("MONGO_DATABASE", "crits")
    return _get_mongo_client()[database_name]["services"]


def _normalize_supported_types(value: Any) -> list[str]:
    if value == "all":
        return ["all"]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return []


def _normalize_config(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


@dataclass(slots=True)
class ServiceRecord:
    """Normalized service metadata record from MongoDB."""

    name: str
    type: str = ""
    description: str = ""
    version: str = ""
    enabled: bool | None = None
    run_on_triage: bool | None = None
    status: str = ""
    supported_types: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    compatability_mode: bool | None = None
    is_triage_run: bool | None = None

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "ServiceRecord":
        return cls(
            name=str(document.get("name", "")),
            type=str(document.get("type", "") or ""),
            description=str(document.get("description", "") or ""),
            version=str(document.get("version", "") or ""),
            enabled=document.get("enabled"),
            run_on_triage=document.get("run_on_triage"),
            status=str(document.get("status", "") or ""),
            supported_types=_normalize_supported_types(document.get("supported_types")),
            config=_normalize_config(document.get("config")),
            compatability_mode=document.get("compatability_mode"),
            is_triage_run=document.get("is_triage_run"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""

        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "run_on_triage": self.run_on_triage,
            "status": self.status,
            "supported_types": list(self.supported_types),
            "config": dict(self.config),
            "compatability_mode": self.compatability_mode,
            "is_triage_run": self.is_triage_run,
        }


def get_service_record(service_name: str) -> ServiceRecord | None:
    """Fetch a single service record by name."""
    document = _get_services_collection().find_one({"name": service_name})
    if not document:
        return None
    return ServiceRecord.from_document(document)


def find_service_records(query: dict[str, Any] | None = None) -> list[ServiceRecord]:
    """Fetch service records matching a MongoDB query."""
    documents = _get_services_collection().find(query or {})
    return [ServiceRecord.from_document(document) for document in documents]


def list_service_names(query: dict[str, Any] | None = None) -> list[str]:
    """Fetch service names matching a MongoDB query."""
    return [record.name for record in find_service_records(query)]


def update_service_record(service_name: str, fields: dict[str, Any]) -> None:
    """Upsert service record fields using a raw MongoDB update."""
    update_fields = dict(fields)
    update_fields.setdefault("schema_version", SERVICE_RECORD_SCHEMA_VERSION)
    _get_services_collection().update_one(
        {"name": service_name},
        {"$set": update_fields},
        upsert=True,
    )
