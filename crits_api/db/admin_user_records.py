"""Raw MongoDB helpers for admin user records."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, MongoClient
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


def _get_users_collection() -> Collection[dict[str, Any]]:
    database_name = os.environ.get("MONGO_DATABASE", "crits")
    return _get_mongo_client()[database_name]["users"]


def _coerce_object_id(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except Exception:
        return None


def _normalize_roles(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(role) for role in value if role is not None]


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    return None


@dataclass(slots=True)
class UserRecord:
    """Normalized admin-facing user record."""

    id: str
    username: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    last_login: datetime | None = None
    date_joined: datetime | None = None
    organization: str = ""
    roles: list[str] = field(default_factory=list)
    totp: bool = False

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> UserRecord:
        return cls(
            id=str(document.get("_id", "")),
            username=str(document.get("username", "") or ""),
            email=str(document.get("email", "") or ""),
            first_name=str(document.get("first_name", "") or ""),
            last_name=str(document.get("last_name", "") or ""),
            is_active=bool(document.get("is_active", True)),
            is_staff=bool(document.get("is_staff", False)),
            is_superuser=bool(document.get("is_superuser", False)),
            last_login=_as_datetime(document.get("last_login")),
            date_joined=_as_datetime(document.get("date_joined")),
            organization=str(document.get("organization", "") or ""),
            roles=_normalize_roles(document.get("roles")),
            totp=bool(document.get("totp", False)),
        )


_USER_PROJECTION = {
    "username": 1,
    "email": 1,
    "first_name": 1,
    "last_name": 1,
    "is_active": 1,
    "is_staff": 1,
    "is_superuser": 1,
    "last_login": 1,
    "date_joined": 1,
    "organization": 1,
    "roles": 1,
    "totp": 1,
}


def list_user_records() -> list[UserRecord]:
    """List admin-visible users sorted by username."""

    documents = _get_users_collection().find({}, _USER_PROJECTION).sort("username", ASCENDING)
    return [UserRecord.from_document(document) for document in documents]


def get_user_record(user_id: str) -> UserRecord | None:
    """Fetch a single user by id."""

    object_id = _coerce_object_id(user_id)
    if object_id is None:
        return None

    document = _get_users_collection().find_one({"_id": object_id}, _USER_PROJECTION)
    if not document:
        return None
    return UserRecord.from_document(document)
