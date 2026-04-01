"""Raw MongoDB helpers for admin user records."""

from __future__ import annotations

import hmac
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from hashlib import sha1
from typing import Any

from bson import ObjectId
from django.conf import settings as django_settings
from django.contrib.auth.hashers import make_password
from pymongo import ASCENDING, MongoClient, ReturnDocument
from pymongo.collection import Collection

USER_SCHEMA_VERSION = 3

_FAVORITES_DEFAULT: dict[str, Any] = {
    "Actor": [],
    "Backdoor": [],
    "Campaign": [],
    "Certificate": [],
    "Domain": [],
    "Email": [],
    "Event": [],
    "Exploit": [],
    "IP": [],
    "Indicator": [],
    "PCAP": [],
    "RawData": [],
    "Sample": [],
    "Screenshot": [],
    "Signature": [],
    "Target": [],
}

_SUBSCRIPTIONS_DEFAULT: dict[str, Any] = {
    "Actor": [],
    "Backdoor": [],
    "Campaign": [],
    "Certificate": [],
    "Domain": [],
    "Email": [],
    "Event": [],
    "Exploit": [],
    "IP": [],
    "Indicator": [],
    "PCAP": [],
    "RawData": [],
    "Sample": [],
    "Signature": [],
    "Source": [],
    "Target": [],
}

_PREFS_DEFAULT: dict[str, Any] = {
    "notify": {"email": False},
    "plugins": {},
    "ui": {"theme": "default", "table_page_size": 25},
    "nav": {
        "nav_menu": "default",
        "text_color": "#FFF",
        "background_color": "#464646",
        "hover_text_color": "#39F",
        "hover_background_color": "#6F6F6F",
    },
    "toast_notifications": {
        "enabled": True,
        "acknowledgement_type": "sticky",
        "initial_notifications_display": "show",
        "newer_notifications_location": "top",
    },
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


def _normalize_email(email: str | None) -> str:
    if not email:
        return ""

    try:
        email_name, domain_part = email.strip().split("@", 1)
    except ValueError:
        return email.strip()
    return "@".join([email_name, domain_part.lower()])


def _generate_default_api_key(now: datetime) -> dict[str, Any]:
    new_uuid = uuid.uuid4()
    key = hmac.new(new_uuid.bytes, digestmod=sha1).hexdigest()
    return {
        "name": "default",
        "api_key": key,
        "date": now,
        "default": True,
    }


def password_is_complex(password: str) -> bool:
    """Return whether a password satisfies the configured complexity regex."""

    return bool(re.compile(django_settings.PASSWORD_COMPLEXITY_REGEX).match(password))


def allow_passwordless_user_creation() -> bool:
    """Return whether REMOTE_USER mode allows passwordless user creation."""

    return bool(django_settings.REMOTE_USER)


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


def _build_new_user_document(
    username: str,
    password: str,
    *,
    email: str = "",
    first_name: str = "",
    last_name: str = "",
    roles: list[str] | None = None,
) -> dict[str, Any] | None:
    now = datetime.now()
    normalized_roles = [str(role) for role in roles or []]
    user_document: dict[str, Any] = {
        "username": username,
        "email": _normalize_email(email),
        "first_name": first_name,
        "last_name": last_name,
        "is_staff": False,
        "is_active": True,
        "is_superuser": False,
        "last_login": now,
        "date_joined": now,
        "invalid_login_attempts": 0,
        "login_attempts": [],
        "organization": str(django_settings.COMPANY_NAME),
        "password_reset": {
            "reset_code": "",
            "attempts": 0,
            "date": now,
        },
        "roles": normalized_roles,
        "subscriptions": dict(_SUBSCRIPTIONS_DEFAULT),
        "favorites": dict(_FAVORITES_DEFAULT),
        "prefs": dict(_PREFS_DEFAULT),
        "acl_needs_update": bool(normalized_roles),
        "acl": {},
        "totp": False,
        "secret": "",
        "api_keys": [_generate_default_api_key(now)],
        "schema_version": USER_SCHEMA_VERSION,
    }

    if password and password_is_complex(password):
        user_document["password"] = make_password(password)
        return user_document

    if allow_passwordless_user_creation():
        return user_document

    return None


def username_exists(username: str) -> bool:
    """Return whether a username already exists."""

    return _get_users_collection().find_one({"username": username}, {"_id": 1}) is not None


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


def create_user_record(
    username: str,
    password: str,
    *,
    email: str = "",
    first_name: str = "",
    last_name: str = "",
    roles: list[str] | None = None,
) -> UserRecord | None:
    """Create a new user record."""

    user_document = _build_new_user_document(
        username,
        password,
        email=email,
        first_name=first_name,
        last_name=last_name,
        roles=roles,
    )
    if user_document is None:
        return None

    insert_result = _get_users_collection().insert_one(user_document)
    user_document["_id"] = insert_result.inserted_id
    return UserRecord.from_document(user_document)


def update_user_record(
    user_id: str,
    *,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    organization: str | None = None,
    is_active: bool | None = None,
    roles: list[str] | None = None,
) -> UserRecord | None:
    """Update mutable admin user fields."""

    object_id = _coerce_object_id(user_id)
    if object_id is None:
        return None

    update_fields: dict[str, Any] = {}
    if email is not None:
        update_fields["email"] = email
    if first_name is not None:
        update_fields["first_name"] = first_name
    if last_name is not None:
        update_fields["last_name"] = last_name
    if organization is not None:
        update_fields["organization"] = organization
    if is_active is not None:
        update_fields["is_active"] = is_active
    if roles is not None:
        update_fields["roles"] = [str(role) for role in roles]
        update_fields["acl_needs_update"] = True

    if not update_fields:
        return get_user_record(user_id)

    document = _get_users_collection().find_one_and_update(
        {"_id": object_id},
        {"$set": update_fields},
        projection=_USER_PROJECTION,
        return_document=ReturnDocument.AFTER,
    )
    if not document:
        return None
    return UserRecord.from_document(document)


def reset_user_password(user_id: str, new_password: str) -> UserRecord | None | bool:
    """Reset a user's password hash if the new password is valid."""

    object_id = _coerce_object_id(user_id)
    if object_id is None:
        return None
    if not password_is_complex(new_password):
        return False

    document = _get_users_collection().find_one_and_update(
        {"_id": object_id},
        {"$set": {"password": make_password(new_password)}},
        projection=_USER_PROJECTION,
        return_document=ReturnDocument.AFTER,
    )
    if not document:
        return None
    return UserRecord.from_document(document)
