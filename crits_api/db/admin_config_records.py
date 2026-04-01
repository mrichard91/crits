"""Raw MongoDB helpers for simple admin config-item collections."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection


class AdminConfigType(str, Enum):
    """Supported raw config-item collection types."""

    RAW_DATA_TYPE = "raw_data_type"
    SIGNATURE_TYPE = "signature_type"
    SIGNATURE_DEPENDENCY = "signature_dependency"
    ACTION = "action"


_COLLECTIONS: dict[AdminConfigType, str] = {
    AdminConfigType.RAW_DATA_TYPE: "raw_data_types",
    AdminConfigType.SIGNATURE_TYPE: "signature_types",
    AdminConfigType.SIGNATURE_DEPENDENCY: "signature_dependency",
    AdminConfigType.ACTION: "idb_actions",
}


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


def _get_collection(config_type: AdminConfigType) -> Collection[dict[str, Any]]:
    database_name = os.environ.get("MONGO_DATABASE", "crits")
    return _get_mongo_client()[database_name][_COLLECTIONS[config_type]]


@dataclass(slots=True)
class AdminConfigRecord:
    """Normalized config-item record."""

    id: str
    name: str
    active: str = "on"

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> AdminConfigRecord:
        return cls(
            id=str(document.get("_id", "")),
            name=str(document.get("name", "") or ""),
            active=str(document.get("active", "on") or "on"),
        )


def list_admin_config_records(config_type: AdminConfigType) -> list[AdminConfigRecord]:
    """List all config items for a collection, sorted by name."""

    cursor = _get_collection(config_type).find({}).sort("name", ASCENDING)
    return [AdminConfigRecord.from_document(document) for document in cursor]


def get_admin_config_record(
    config_type: AdminConfigType,
    name: str,
) -> AdminConfigRecord | None:
    """Fetch a config item by name."""

    document = _get_collection(config_type).find_one({"name": name})
    if not document:
        return None
    return AdminConfigRecord.from_document(document)


def create_admin_config_record(
    config_type: AdminConfigType,
    name: str,
    *,
    active: str = "on",
) -> AdminConfigRecord:
    """Create a config item and return the inserted record."""

    insert_result = _get_collection(config_type).insert_one({"name": name, "active": active})
    return AdminConfigRecord(id=str(insert_result.inserted_id), name=name, active=active)


def update_admin_config_record_active(
    config_type: AdminConfigType,
    name: str,
    *,
    active: bool,
) -> AdminConfigRecord | None:
    """Update the active state for a config item."""

    active_value = "on" if active else "off"
    result = _get_collection(config_type).find_one_and_update(
        {"name": name},
        {"$set": {"active": active_value}},
        return_document=True,
    )
    if not result:
        return None
    return AdminConfigRecord.from_document(result)


def delete_admin_config_record(config_type: AdminConfigType, name: str) -> str | None:
    """Delete a config item by name and return its id if found."""

    document = _get_collection(config_type).find_one({"name": name}, {"_id": 1})
    if not document:
        return None

    deleted_id = str(document.get("_id", ""))
    _get_collection(config_type).delete_one({"_id": ObjectId(deleted_id)})
    return deleted_id
