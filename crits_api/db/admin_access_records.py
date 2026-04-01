"""Raw MongoDB helpers for admin source and role records."""

from __future__ import annotations

import os
from copy import deepcopy
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, MongoClient, ReturnDocument
from pymongo.collection import Collection

SOURCE_ACCESS_SCHEMA_VERSION = 1
ROLE_SCHEMA_VERSION = 1

ROLE_MUTABLE_PERMISSION_FIELDS = {
    "api_interface",
    "script_interface",
    "web_interface",
    "add_new_actor_identifier_type",
    "add_new_indicator_action",
    "add_new_raw_data_type",
    "add_new_signature_dependency",
    "add_new_signature_type",
    "add_new_source",
    "add_new_user_role",
    "add_new_tlds",
    "control_panel_read",
    "control_panel_system_read",
    "control_panel_general_read",
    "control_panel_general_edit",
    "control_panel_crits_read",
    "control_panel_crits_edit",
    "control_panel_ldap_read",
    "control_panel_ldap_edit",
    "control_panel_security_read",
    "control_panel_security_edit",
    "control_panel_downloading_read",
    "control_panel_downloading_edit",
    "control_panel_system_services_read",
    "control_panel_system_services_edit",
    "control_panel_logging_read",
    "control_panel_logging_edit",
    "control_panel_items_read",
    "control_panel_users_read",
    "control_panel_users_add",
    "control_panel_users_edit",
    "control_panel_users_active",
    "control_panel_roles_read",
    "control_panel_roles_edit",
    "control_panel_services_read",
    "control_panel_services_edit",
    "control_panel_audit_log_read",
    "recent_activity_read",
    "stix_import_add",
    "dns_timeline_read",
    "emails_timeline_read",
    "indicators_timeline_read",
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


def _get_collection(name: str) -> Collection[dict[str, Any]]:
    database_name = os.environ.get("MONGO_DATABASE", "crits")
    return _get_mongo_client()[database_name][name]


def _get_sources_collection() -> Collection[dict[str, Any]]:
    return _get_collection("source_access")


def _get_roles_collection() -> Collection[dict[str, Any]]:
    return _get_collection("roles")


def _as_bool(value: Any) -> bool:
    return bool(value)


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _coerce_object_id(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except Exception:
        return None


@dataclass(slots=True)
class SourceAccessRecord:
    """Normalized source-access record."""

    id: str
    name: str
    active: str = "on"
    sample_count: int = 0

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> SourceAccessRecord:
        return cls(
            id=str(document.get("_id", "")),
            name=str(document.get("name", "") or ""),
            active=str(document.get("active", "on") or "on"),
            sample_count=_as_int(document.get("sample_count", 0)),
        )


@dataclass(slots=True)
class RoleSourceACLRecord:
    """Normalized embedded role source ACL."""

    name: str
    read: bool = False
    write: bool = False
    tlp_red: bool = False
    tlp_amber: bool = False
    tlp_green: bool = False

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> RoleSourceACLRecord:
        return cls(
            name=str(document.get("name", "") or ""),
            read=_as_bool(document.get("read", False)),
            write=_as_bool(document.get("write", False)),
            tlp_red=_as_bool(document.get("tlp_red", False)),
            tlp_amber=_as_bool(document.get("tlp_amber", False)),
            tlp_green=_as_bool(document.get("tlp_green", False)),
        )

    def to_document(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "read": self.read,
            "write": self.write,
            "tlp_red": self.tlp_red,
            "tlp_amber": self.tlp_amber,
            "tlp_green": self.tlp_green,
        }


def _normalize_role_sources(value: Any) -> list[RoleSourceACLRecord]:
    if not isinstance(value, list):
        return []
    return [
        RoleSourceACLRecord.from_document(source) for source in value if isinstance(source, dict)
    ]


@dataclass(slots=True)
class RoleRecord:
    """Normalized role record used by admin GraphQL."""

    id: str
    name: str
    active: str = "on"
    description: str = ""
    sources: list[RoleSourceACLRecord] = field(default_factory=list)
    api_interface: bool = False
    script_interface: bool = False
    web_interface: bool = False
    control_panel_read: bool = False
    control_panel_users_read: bool = False
    control_panel_users_add: bool = False
    control_panel_users_edit: bool = False
    control_panel_roles_read: bool = False
    control_panel_roles_edit: bool = False
    control_panel_services_read: bool = False
    control_panel_services_edit: bool = False
    control_panel_audit_log_read: bool = False

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> RoleRecord:
        return cls(
            id=str(document.get("_id", "")),
            name=str(document.get("name", "") or ""),
            active=str(document.get("active", "on") or "on"),
            description=str(document.get("description", "") or ""),
            sources=_normalize_role_sources(document.get("sources")),
            api_interface=_as_bool(document.get("api_interface", False)),
            script_interface=_as_bool(document.get("script_interface", False)),
            web_interface=_as_bool(document.get("web_interface", False)),
            control_panel_read=_as_bool(document.get("control_panel_read", False)),
            control_panel_users_read=_as_bool(document.get("control_panel_users_read", False)),
            control_panel_users_add=_as_bool(document.get("control_panel_users_add", False)),
            control_panel_users_edit=_as_bool(document.get("control_panel_users_edit", False)),
            control_panel_roles_read=_as_bool(document.get("control_panel_roles_read", False)),
            control_panel_roles_edit=_as_bool(document.get("control_panel_roles_edit", False)),
            control_panel_services_read=_as_bool(
                document.get("control_panel_services_read", False)
            ),
            control_panel_services_edit=_as_bool(
                document.get("control_panel_services_edit", False)
            ),
            control_panel_audit_log_read=_as_bool(
                document.get("control_panel_audit_log_read", False)
            ),
        )


def list_source_access_records() -> list[SourceAccessRecord]:
    """List sources sorted by name."""

    documents = _get_sources_collection().find({}).sort("name", ASCENDING)
    return [SourceAccessRecord.from_document(document) for document in documents]


def get_source_access_record(name: str) -> SourceAccessRecord | None:
    """Fetch a source by name."""

    document = _get_sources_collection().find_one({"name": name})
    if not document:
        return None
    return SourceAccessRecord.from_document(document)


def create_source_access_record(name: str, *, active: str = "on") -> SourceAccessRecord:
    """Create a new source-access record."""

    insert_result = _get_sources_collection().insert_one(
        {
            "name": name,
            "active": active,
            "sample_count": 0,
            "schema_version": SOURCE_ACCESS_SCHEMA_VERSION,
        }
    )
    return SourceAccessRecord(
        id=str(insert_result.inserted_id),
        name=name,
        active=active,
        sample_count=0,
    )


def update_source_access_active(name: str, *, active: bool) -> SourceAccessRecord | None:
    """Toggle a source-access record's active state."""

    document = _get_sources_collection().find_one_and_update(
        {"name": name},
        {"$set": {"active": "on" if active else "off"}},
        return_document=ReturnDocument.AFTER,
    )
    if not document:
        return None
    return SourceAccessRecord.from_document(document)


def list_role_records() -> list[RoleRecord]:
    """List roles sorted by name."""

    documents = _get_roles_collection().find({}).sort("name", ASCENDING)
    return [RoleRecord.from_document(document) for document in documents]


def get_role_record(role_id: str) -> RoleRecord | None:
    """Fetch a role by id."""

    object_id = _coerce_object_id(role_id)
    if object_id is None:
        return None

    document = _get_roles_collection().find_one({"_id": object_id})
    if not document:
        return None
    return RoleRecord.from_document(document)


def get_role_record_by_name(name: str) -> RoleRecord | None:
    """Fetch a role by name."""

    document = _get_roles_collection().find_one({"name": name})
    if not document:
        return None
    return RoleRecord.from_document(document)


def role_name_exists(name: str, *, exclude_id: str | None = None) -> bool:
    """Return whether a role name already exists."""

    query: dict[str, Any] = {"name": name}
    if exclude_id:
        object_id = _coerce_object_id(exclude_id)
        if object_id is not None:
            query["_id"] = {"$ne": object_id}
    return _get_roles_collection().find_one(query, {"_id": 1}) is not None


def _reset_role_value(value: Any) -> Any:
    if isinstance(value, bool):
        return False
    if isinstance(value, dict):
        return {key: _reset_role_value(inner_value) for key, inner_value in value.items()}
    if isinstance(value, list):
        return []
    return value


@lru_cache(maxsize=1)
def _get_role_template_document() -> dict[str, Any]:
    template = _get_roles_collection().find_one({}, sort=[("name", ASCENDING)])
    if not template:
        return {}
    template.pop("_id", None)
    return template


def _build_fallback_role_document(name: str, description: str) -> dict[str, Any]:
    document: dict[str, Any] = {
        "name": name,
        "description": description,
        "active": "on",
        "schema_version": ROLE_SCHEMA_VERSION,
        "sources": [],
    }
    for permission_name in ROLE_MUTABLE_PERMISSION_FIELDS:
        document[permission_name] = False
    return document


def _build_new_role_document(name: str, description: str) -> dict[str, Any]:
    template = deepcopy(_get_role_template_document())
    if not template:
        return _build_fallback_role_document(name, description)

    new_document: dict[str, Any] = {}
    for key, value in template.items():
        if key == "name":
            new_document[key] = name
        elif key == "description":
            new_document[key] = description
        elif key == "active":
            new_document[key] = "on"
        elif key == "schema_version":
            new_document[key] = ROLE_SCHEMA_VERSION
        elif key == "sources":
            new_document[key] = []
        else:
            new_document[key] = _reset_role_value(value)

    new_document.setdefault("name", name)
    new_document.setdefault("description", description)
    new_document.setdefault("active", "on")
    new_document.setdefault("schema_version", ROLE_SCHEMA_VERSION)
    new_document.setdefault("sources", [])
    return new_document


def create_role_record(name: str, *, description: str = "") -> RoleRecord:
    """Create a role record with the legacy default shape."""

    new_document = _build_new_role_document(name, description)
    insert_result = _get_roles_collection().insert_one(new_document)
    new_document["_id"] = insert_result.inserted_id
    return RoleRecord.from_document(new_document)


def update_role_record(
    role_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
    active: bool | None = None,
) -> RoleRecord | None:
    """Update top-level role fields."""

    object_id = _coerce_object_id(role_id)
    if object_id is None:
        return None

    update_fields: dict[str, Any] = {}
    if name is not None:
        update_fields["name"] = name
    if description is not None:
        update_fields["description"] = description
    if active is not None:
        update_fields["active"] = "on" if active else "off"

    if not update_fields:
        return get_role_record(role_id)

    document = _get_roles_collection().find_one_and_update(
        {"_id": object_id},
        {"$set": update_fields},
        return_document=ReturnDocument.AFTER,
    )
    if not document:
        return None
    return RoleRecord.from_document(document)


def upsert_role_source(
    role_id: str,
    *,
    source_name: str,
    read: bool,
    write: bool,
    tlp_red: bool,
    tlp_amber: bool,
    tlp_green: bool,
) -> RoleRecord | None:
    """Add or update a source ACL on a role."""

    object_id = _coerce_object_id(role_id)
    if object_id is None:
        return None

    document = _get_roles_collection().find_one({"_id": object_id})
    if not document:
        return None

    sources = _normalize_role_sources(document.get("sources"))
    existing = next((source for source in sources if source.name == source_name), None)
    if existing:
        existing.read = read
        existing.write = write
        existing.tlp_red = tlp_red
        existing.tlp_amber = tlp_amber
        existing.tlp_green = tlp_green
    elif get_source_access_record(source_name):
        sources.append(
            RoleSourceACLRecord(
                name=source_name,
                read=read,
                write=write,
                tlp_red=tlp_red,
                tlp_amber=tlp_amber,
                tlp_green=tlp_green,
            )
        )

    stored_sources = [source.to_document() for source in sources]
    updated_document = _get_roles_collection().find_one_and_update(
        {"_id": object_id},
        {"$set": {"sources": stored_sources}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_document:
        return None
    return RoleRecord.from_document(updated_document)


def remove_role_source(role_id: str, *, source_name: str) -> RoleRecord | None:
    """Remove a source ACL from a role."""

    object_id = _coerce_object_id(role_id)
    if object_id is None:
        return None

    document = _get_roles_collection().find_one({"_id": object_id})
    if not document:
        return None

    sources = [
        source.to_document()
        for source in _normalize_role_sources(document.get("sources"))
        if source.name != source_name
    ]
    updated_document = _get_roles_collection().find_one_and_update(
        {"_id": object_id},
        {"$set": {"sources": sources}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_document:
        return None
    return RoleRecord.from_document(updated_document)


def is_valid_role_permission(permission: str) -> bool:
    """Return whether a permission is a supported top-level role boolean."""

    return permission in ROLE_MUTABLE_PERMISSION_FIELDS


def update_role_permission(role_id: str, *, permission: str, value: bool) -> RoleRecord | None:
    """Update a top-level boolean permission on a role."""

    object_id = _coerce_object_id(role_id)
    if object_id is None:
        return None

    updated_document = _get_roles_collection().find_one_and_update(
        {"_id": object_id},
        {"$set": {permission: value}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_document:
        return None
    return RoleRecord.from_document(updated_document)
