"""
Admin configuration GraphQL types for CRITs API.

Types for source access, roles, simple config items, and vocabularies.
"""

from enum import Enum
from typing import Any

import strawberry


@strawberry.type
class SourceAccessType:
    """A data source that can be assigned to roles and TLOs."""

    name: str
    active: bool
    sample_count: int = 0

    @classmethod
    def from_model(cls, obj: Any) -> "SourceAccessType":
        return cls(
            name=getattr(obj, "name", "") or "",
            active=getattr(obj, "active", "on") == "on",
            sample_count=getattr(obj, "sample_count", 0) or 0,
        )


@strawberry.type
class EmbeddedSourceACLType:
    """Source access control entry within a role."""

    name: str
    read: bool = False
    write: bool = False
    tlp_red: bool = False
    tlp_amber: bool = False
    tlp_green: bool = False

    @classmethod
    def from_model(cls, obj: Any) -> "EmbeddedSourceACLType":
        return cls(
            name=getattr(obj, "name", "") or "",
            read=bool(getattr(obj, "read", False)),
            write=bool(getattr(obj, "write", False)),
            tlp_red=bool(getattr(obj, "tlp_red", False)),
            tlp_amber=bool(getattr(obj, "tlp_amber", False)),
            tlp_green=bool(getattr(obj, "tlp_green", False)),
        )


@strawberry.type
class RoleType:
    """A user role with permissions and source access."""

    id: str
    name: str
    active: bool
    description: str = ""
    sources: list[EmbeddedSourceACLType] = strawberry.field(default_factory=list)

    # Interface permissions
    api_interface: bool = False
    script_interface: bool = False
    web_interface: bool = False

    # Control panel permissions
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
    def from_model(cls, obj: Any) -> "RoleType":
        sources = []
        if hasattr(obj, "sources") and obj.sources:
            for s in obj.sources:
                sources.append(EmbeddedSourceACLType.from_model(s))

        return cls(
            id=str(obj.id),
            name=getattr(obj, "name", "") or "",
            active=getattr(obj, "active", "on") == "on",
            description=getattr(obj, "description", "") or "",
            sources=sources,
            api_interface=bool(getattr(obj, "api_interface", False)),
            script_interface=bool(getattr(obj, "script_interface", False)),
            web_interface=bool(getattr(obj, "web_interface", False)),
            control_panel_read=bool(getattr(obj, "control_panel_read", False)),
            control_panel_users_read=bool(getattr(obj, "control_panel_users_read", False)),
            control_panel_users_add=bool(getattr(obj, "control_panel_users_add", False)),
            control_panel_users_edit=bool(getattr(obj, "control_panel_users_edit", False)),
            control_panel_roles_read=bool(getattr(obj, "control_panel_roles_read", False)),
            control_panel_roles_edit=bool(getattr(obj, "control_panel_roles_edit", False)),
            control_panel_services_read=bool(getattr(obj, "control_panel_services_read", False)),
            control_panel_services_edit=bool(getattr(obj, "control_panel_services_edit", False)),
            control_panel_audit_log_read=bool(getattr(obj, "control_panel_audit_log_read", False)),
        )


@strawberry.type
class NamedConfigType:
    """Generic config item with name and active status (RawDataType, SignatureType, etc.)."""

    name: str
    active: bool

    @classmethod
    def from_model(cls, obj: Any) -> "NamedConfigType":
        return cls(
            name=getattr(obj, "name", "") or "",
            active=getattr(obj, "active", "on") == "on",
        )


@strawberry.enum
class ConfigTypeEnum(Enum):
    """Enum for parameterized config item mutations."""

    RAW_DATA_TYPE = "raw_data_type"
    SIGNATURE_TYPE = "signature_type"
    SIGNATURE_DEPENDENCY = "signature_dependency"
    ACTION = "action"
