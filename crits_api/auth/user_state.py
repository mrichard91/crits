"""Lightweight authenticated user objects backed by raw Mongo records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from crits_api.db.auth_records import AuthUserRecord, get_role_acl_documents


@dataclass(slots=True)
class SourceACL:
    """User access flags for a single source."""

    name: str
    read: bool = False
    write: bool = False
    tlp_red: bool = False
    tlp_amber: bool = False
    tlp_green: bool = False


@dataclass(slots=True)
class AuthenticatedUser:
    """Request-time authenticated user state for GraphQL and REST routes."""

    id: str
    username: str
    is_active: bool
    is_staff: bool
    is_superuser: bool
    organization: str
    roles: list[str] = field(default_factory=list)
    totp: bool = False
    secret: str = ""
    acl: dict[str, Any] = field(default_factory=dict)
    source_acls: list[SourceACL] = field(default_factory=list)

    def get_access_list(self, update: bool = False) -> dict[str, Any]:
        """Return the merged ACL."""

        return self.acl

    def get_sources_list(self) -> list[str]:
        """Return readable source names for the user."""

        return [source.name for source in self.source_acls]

    def has_access_to(self, attribute: str | None = None) -> bool:
        """Check whether the user has the specified ACL attribute."""

        if self.is_superuser:
            return True
        if not attribute:
            return False

        attr: Any = self.acl
        for part in attribute.split("."):
            if isinstance(attr, dict):
                attr = attr.get(part, False)
            else:
                return False
        return bool(attr)

    def filter_dict_source_tlp(self, filter_dict: dict[str, Any]) -> dict[str, Any]:
        """Apply the legacy source/TLP filter to a Mongo query dict."""

        if self.is_superuser:
            return filter_dict

        user_source_list_red = [
            source.name for source in self.source_acls if source.tlp_red and source.read
        ]
        user_source_list_amber = [
            source.name for source in self.source_acls if source.tlp_amber and source.read
        ]
        user_source_list_green = [
            source.name for source in self.source_acls if source.tlp_green and source.read
        ]

        source_tlp_filter = {
            "$elemMatch": {
                "$or": [
                    {"instances.tlp": "white"},
                    {
                        "name": {"$in": user_source_list_red},
                        "instances": {"$elemMatch": {"tlp": {"$exists": False}}},
                    },
                    {"name": {"$in": user_source_list_red}, "instances.tlp": "red"},
                    {"name": {"$in": user_source_list_amber}, "instances.tlp": "amber"},
                    {"name": {"$in": user_source_list_green}, "instances.tlp": "green"},
                ]
            }
        }
        return {"$and": [filter_dict, {"source": source_tlp_filter}]}

    def check_source_tlp(self, obj: Any) -> bool:
        """Check whether the user can read an object based on source/TLP."""

        if self.is_superuser:
            return True
        object_sources = getattr(obj, "source", []) or []

        for source in object_sources:
            source_name = getattr(source, "name", None)
            if not source_name:
                continue

            user_source = next(
                (candidate for candidate in self.source_acls if candidate.name == source_name), None
            )
            if user_source is None:
                continue

            instances = getattr(source, "instances", []) or []
            for instance in instances:
                tlp = getattr(instance, "tlp", "red")
                if tlp == "white":
                    return True
                if tlp == "red" and user_source.tlp_red and user_source.read:
                    return True
                if tlp == "amber" and user_source.tlp_amber and user_source.read:
                    return True
                if tlp == "green" and user_source.tlp_green and user_source.read:
                    return True
        return False


def _merge_role_documents(
    role_documents: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[SourceACL]]:
    acl: dict[str, Any] = {}
    sources: dict[str, SourceACL] = {}

    for role_document in role_documents:
        for key, value in role_document.items():
            if key in {
                "_id",
                "name",
                "description",
                "active",
                "schema_version",
                "unsupported_attrs",
            }:
                continue

            if key == "sources":
                if not isinstance(value, list):
                    continue
                for source in value:
                    if not isinstance(source, dict):
                        continue
                    name = str(source.get("name", "") or "")
                    if not name:
                        continue
                    current = sources.setdefault(name, SourceACL(name=name))
                    current.read = current.read or bool(source.get("read", False))
                    current.write = current.write or bool(source.get("write", False))
                    current.tlp_red = current.tlp_red or bool(source.get("tlp_red", False))
                    current.tlp_amber = current.tlp_amber or bool(source.get("tlp_amber", False))
                    current.tlp_green = current.tlp_green or bool(source.get("tlp_green", False))
                continue

            if isinstance(value, dict):
                embedded = acl.setdefault(key, {})
                for inner_key, inner_value in value.items():
                    if isinstance(inner_value, bool):
                        embedded[inner_key] = bool(embedded.get(inner_key, False) or inner_value)
                    elif inner_key not in embedded:
                        embedded[inner_key] = inner_value
                continue

            if isinstance(value, bool):
                acl[key] = bool(acl.get(key, False) or value)

    source_list = sorted(sources.values(), key=lambda source: source.name)
    acl["sources"] = source_list
    return acl, source_list


def build_authenticated_user(user_record: AuthUserRecord) -> AuthenticatedUser:
    """Build a lightweight authenticated user from raw user and role records."""

    role_documents = get_role_acl_documents(user_record.roles)
    acl, source_acls = _merge_role_documents(role_documents)
    return AuthenticatedUser(
        id=user_record.id,
        username=user_record.username,
        is_active=user_record.is_active,
        is_staff=user_record.is_staff,
        is_superuser=user_record.is_superuser,
        organization=user_record.organization,
        roles=list(user_record.roles),
        totp=user_record.totp,
        secret=user_record.secret,
        acl=acl,
        source_acls=source_acls,
    )
