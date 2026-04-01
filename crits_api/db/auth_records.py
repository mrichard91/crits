"""Raw MongoDB helpers for authentication and session-backed user state."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any

from bson import ObjectId
from pymongo import MongoClient, ReturnDocument
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


def _get_collection(name: str) -> Collection[dict[str, Any]]:
    database_name = os.environ.get("MONGO_DATABASE", "crits")
    return _get_mongo_client()[database_name][name]


def _get_users_collection() -> Collection[dict[str, Any]]:
    return _get_collection("users")


def _get_roles_collection() -> Collection[dict[str, Any]]:
    return _get_collection("roles")


def _get_config_collection() -> Collection[dict[str, Any]]:
    return _get_collection("config")


def _coerce_object_id(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except Exception:
        return None


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    return None


@dataclass(slots=True)
class AuthConfig:
    """Authentication-relevant runtime configuration."""

    ldap_auth: bool = False
    ldap_tls: bool = False
    ldap_server: str = ""
    ldap_bind_dn: str = ""
    ldap_bind_password: str = ""
    ldap_usercn: str = ""
    ldap_userdn: str = ""
    ldap_update_on_login: bool = False
    invalid_login_attempts: int = 3
    password_complexity_regex: str = (
        r"(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$"
    )
    session_timeout_hours: int = 12
    totp_web: str = "Disabled"
    create_unknown_user: bool = False
    remote_user: bool = False

    @property
    def invalid_login_threshold(self) -> int:
        """Return the threshold used for disabling an account on password failures."""

        return max(0, self.invalid_login_attempts - 1)


@dataclass(slots=True)
class AuthUserRecord:
    """Normalized auth/session user document."""

    id: str
    username: str
    password: str = ""
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    organization: str = ""
    roles: list[str] = field(default_factory=list)
    acl: dict[str, Any] = field(default_factory=dict)
    acl_needs_update: bool = False
    invalid_login_attempts: int = 0
    login_attempts: list[dict[str, Any]] = field(default_factory=list)
    password_reset: dict[str, Any] = field(default_factory=dict)
    totp: bool = False
    secret: str = ""

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> AuthUserRecord:
        return cls(
            id=str(document.get("_id", "")),
            username=str(document.get("username", "") or ""),
            password=str(document.get("password", "") or ""),
            is_active=bool(document.get("is_active", True)),
            is_staff=bool(document.get("is_staff", False)),
            is_superuser=bool(document.get("is_superuser", False)),
            organization=str(document.get("organization", "") or ""),
            roles=[str(role) for role in document.get("roles", []) or []],
            acl=dict(document.get("acl", {}) or {}),
            acl_needs_update=bool(document.get("acl_needs_update", False)),
            invalid_login_attempts=int(document.get("invalid_login_attempts", 0) or 0),
            login_attempts=[
                dict(attempt)
                for attempt in document.get("login_attempts", []) or []
                if isinstance(attempt, dict)
            ],
            password_reset=dict(document.get("password_reset", {}) or {}),
            totp=bool(document.get("totp", False)),
            secret=str(document.get("secret", "") or ""),
        )


_AUTH_USER_PROJECTION = {
    "username": 1,
    "password": 1,
    "is_active": 1,
    "is_staff": 1,
    "is_superuser": 1,
    "organization": 1,
    "roles": 1,
    "acl": 1,
    "acl_needs_update": 1,
    "invalid_login_attempts": 1,
    "login_attempts": 1,
    "password_reset": 1,
    "totp": 1,
    "secret": 1,
}


def get_auth_config() -> AuthConfig:
    """Load auth-related runtime config from the config collection."""

    document = _get_config_collection().find_one({}) or {}
    return AuthConfig(
        ldap_auth=bool(document.get("ldap_auth", False)),
        ldap_tls=bool(document.get("ldap_tls", False)),
        ldap_server=str(document.get("ldap_server", "") or ""),
        ldap_bind_dn=str(document.get("ldap_bind_dn", "") or ""),
        ldap_bind_password=str(document.get("ldap_bind_password", "") or ""),
        ldap_usercn=str(document.get("ldap_usercn", "") or ""),
        ldap_userdn=str(document.get("ldap_userdn", "") or ""),
        ldap_update_on_login=bool(document.get("ldap_update_on_login", False)),
        invalid_login_attempts=int(document.get("invalid_login_attempts", 3) or 3),
        password_complexity_regex=str(
            document.get(
                "password_complexity_regex",
                r"(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$",
            )
        ),
        session_timeout_hours=int(document.get("session_timeout", 12) or 12),
        totp_web=str(document.get("totp_web", "Disabled") or "Disabled"),
        create_unknown_user=bool(document.get("create_unknown_user", False)),
        remote_user=bool(document.get("remote_user", False)),
    )


def get_auth_user_by_username(username: str) -> AuthUserRecord | None:
    """Fetch a single auth user by username."""

    document = _get_users_collection().find_one({"username": username}, _AUTH_USER_PROJECTION)
    if not document:
        return None
    return AuthUserRecord.from_document(document)


def get_auth_user_by_id(user_id: str) -> AuthUserRecord | None:
    """Fetch a single auth user by id."""

    object_id = _coerce_object_id(user_id)
    if object_id is None:
        return None

    document = _get_users_collection().find_one({"_id": object_id}, _AUTH_USER_PROJECTION)
    if not document:
        return None
    return AuthUserRecord.from_document(document)


def get_role_acl_documents(role_names: list[str]) -> list[dict[str, Any]]:
    """Fetch full role documents for ACL merging."""

    if not role_names:
        return []
    return list(_get_roles_collection().find({"name": {"$in": role_names}}))


def update_auth_user_by_id(
    user_id: str,
    *,
    set_fields: dict[str, Any] | None = None,
    append_login_attempt: dict[str, Any] | None = None,
) -> AuthUserRecord | None:
    """Apply auth-related updates to a user by id and return the updated record."""

    object_id = _coerce_object_id(user_id)
    if object_id is None:
        return None

    update: dict[str, Any] = {}
    if set_fields:
        update["$set"] = dict(set_fields)
    if append_login_attempt:
        update["$push"] = {
            "login_attempts": {
                "$each": [dict(append_login_attempt)],
                "$slice": -50,
            }
        }

    if not update:
        return get_auth_user_by_id(user_id)

    document = _get_users_collection().find_one_and_update(
        {"_id": object_id},
        update,
        projection=_AUTH_USER_PROJECTION,
        return_document=ReturnDocument.AFTER,
    )
    if not document:
        return None
    return AuthUserRecord.from_document(document)


def update_auth_user_by_username(
    username: str,
    *,
    set_fields: dict[str, Any] | None = None,
) -> AuthUserRecord | None:
    """Apply auth-related updates to a user by username and return the updated record."""

    if not set_fields:
        return get_auth_user_by_username(username)

    document = _get_users_collection().find_one_and_update(
        {"username": username},
        {"$set": dict(set_fields)},
        projection=_AUTH_USER_PROJECTION,
        return_document=ReturnDocument.AFTER,
    )
    if not document:
        return None
    return AuthUserRecord.from_document(document)
