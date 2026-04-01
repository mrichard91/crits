"""Raw Mongo helpers for common TLO GraphQL query patterns."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from types import SimpleNamespace
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, MongoClient
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


def get_tlo_collection(name: str) -> Collection[dict[str, Any]]:
    """Return a raw Mongo collection handle for the configured CRITs DB."""

    database_name = os.environ.get("MONGO_DATABASE", "crits")
    return _get_mongo_client()[database_name][name]


def coerce_object_id(value: str) -> ObjectId | None:
    """Convert a string to ObjectId when valid."""

    try:
        return ObjectId(value)
    except Exception:
        return None


def build_contains_filter(field: str, value: str | None) -> dict[str, Any]:
    """Build a case-insensitive contains filter for a field."""

    if not value:
        return {}
    return {field: {"$regex": re.escape(value), "$options": "i"}}


def combine_filters(*filters: dict[str, Any]) -> dict[str, Any]:
    """Combine raw Mongo filters into a single `$and` expression when needed."""

    parts: list[dict[str, Any]] = []
    for filter_dict in filters:
        if not filter_dict:
            continue
        and_parts = filter_dict.get("$and")
        if isinstance(and_parts, list) and len(filter_dict) == 1:
            for part in and_parts:
                if part:
                    parts.append(part)
            continue
        parts.append(filter_dict)

    if not parts:
        return {}
    if len(parts) == 1:
        return parts[0]
    return {"$and": parts}


def raw_sort_spec(
    sort_by: str | None,
    sort_dir: str | None,
    allowed_fields: dict[str, str],
) -> list[tuple[str, int]]:
    """Resolve GraphQL sort parameters into a PyMongo sort spec."""

    if sort_by and sort_by in allowed_fields:
        direction = DESCENDING if sort_dir == "desc" else ASCENDING
        return [(allowed_fields[sort_by], direction)]
    return [("modified", DESCENDING)]


def get_tlo_record(
    collection_name: str,
    record_id: str,
    *,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Fetch a single TLO document by id with optional extra filtering."""

    object_id = coerce_object_id(record_id)
    if object_id is None:
        return None

    return get_tlo_collection(collection_name).find_one(
        combine_filters({"_id": object_id}, filters or {})
    )


def list_tlo_records(
    collection_name: str,
    *,
    filters: dict[str, Any] | None = None,
    limit: int = 25,
    offset: int = 0,
    sort_by: str | None = None,
    sort_dir: str | None = None,
    allowed_sort_fields: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """List raw TLO documents with filtering, sorting, and pagination."""

    cursor = get_tlo_collection(collection_name).find(filters or {})
    sort_spec = raw_sort_spec(sort_by, sort_dir, allowed_sort_fields or {})
    return list(cursor.sort(sort_spec).skip(offset).limit(limit))


def count_tlo_records(
    collection_name: str,
    *,
    filters: dict[str, Any] | None = None,
) -> int:
    """Count raw TLO documents matching the filter."""

    return int(get_tlo_collection(collection_name).count_documents(filters or {}))


def distinct_tlo_values(
    collection_name: str,
    field: str,
    *,
    filters: dict[str, Any] | None = None,
) -> list[str]:
    """Get sorted distinct string values for a field."""

    values = get_tlo_collection(collection_name).distinct(field, filters or {})
    return sorted(str(value) for value in values if value)


def to_model_namespace(value: Any) -> Any:
    """Convert nested raw Mongo values into attribute-access objects for GraphQL types."""

    if isinstance(value, dict):
        converted = {key: to_model_namespace(item) for key, item in value.items() if key != "_id"}
        if "_id" in value:
            converted["id"] = value["_id"]
        return SimpleNamespace(**converted)
    if isinstance(value, list):
        return [to_model_namespace(item) for item in value]
    return value
