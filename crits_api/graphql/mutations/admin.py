"""
Admin configuration mutations for CRITs GraphQL API.

CRUD mutations for sources, roles, and simple config types.
"""

import logging
from typing import Any

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_admin
from crits_api.graphql.types.admin import ConfigTypeEnum
from crits_api.graphql.types.common import DeleteResult, MutationResult

logger = logging.getLogger(__name__)


def _get_config_model(config_type: ConfigTypeEnum) -> Any:
    """Return the MongoEngine document class for a config type."""
    if config_type == ConfigTypeEnum.RAW_DATA_TYPE:
        from crits.raw_data.raw_data import RawDataType

        return RawDataType
    elif config_type == ConfigTypeEnum.SIGNATURE_TYPE:
        from crits.signatures.signature import SignatureType

        return SignatureType
    elif config_type == ConfigTypeEnum.SIGNATURE_DEPENDENCY:
        from crits.signatures.signature import SignatureDependency

        return SignatureDependency
    elif config_type == ConfigTypeEnum.ACTION:
        from crits.core.crits_mongoengine import Action

        return Action
    else:
        raise ValueError(f"Unknown config type: {config_type}")


@strawberry.type
class AdminMutations:
    """Admin configuration mutations."""

    # ── Sources ──────────────────────────────────────────────────────

    @strawberry.mutation(description="Create a new source")
    @require_admin
    def create_source(self, info: Info, name: str) -> MutationResult:
        from crits.core.source_access import SourceAccess

        try:
            existing = SourceAccess.objects(name=name).first()
            if existing:
                return MutationResult(success=False, message=f"Source '{name}' already exists")

            source = SourceAccess(name=name, active="on")
            source.save()
            return MutationResult(
                success=True,
                message=f"Source '{name}' created",
                id=str(source.id),
            )
        except Exception as e:
            logger.error(f"Error creating source: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Toggle a source active/inactive")
    @require_admin
    def toggle_source(self, info: Info, name: str, active: bool) -> MutationResult:
        from crits.core.source_access import SourceAccess

        try:
            source = SourceAccess.objects(name=name).first()
            if not source:
                return MutationResult(success=False, message=f"Source '{name}' not found")

            source.active = "on" if active else "off"
            source.save()
            return MutationResult(
                success=True,
                message=f"Source '{name}' {'activated' if active else 'deactivated'}",
            )
        except Exception as e:
            logger.error(f"Error toggling source: {e}")
            return MutationResult(success=False, message=str(e))

    # ── Roles ────────────────────────────────────────────────────────

    @strawberry.mutation(description="Create a new role")
    @require_admin
    def create_role(self, info: Info, name: str, description: str | None = None) -> MutationResult:
        from crits.core.role import Role

        try:
            existing = Role.objects(name=name).first()
            if existing:
                return MutationResult(success=False, message=f"Role '{name}' already exists")

            role = Role(name=name, active="on")
            if description:
                role.description = description
            role.save()
            return MutationResult(
                success=True,
                message=f"Role '{name}' created",
                id=str(role.id),
            )
        except Exception as e:
            logger.error(f"Error creating role: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update a role's name and/or description")
    @require_admin
    def update_role(
        self,
        info: Info,
        id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> MutationResult:
        from bson import ObjectId

        from crits.core.role import Role

        try:
            role = Role.objects(id=ObjectId(id)).first()
            if not role:
                return MutationResult(success=False, message="Role not found")

            if name is not None:
                # Check for duplicate name
                dup = Role.objects(name=name, id__ne=ObjectId(id)).first()
                if dup:
                    return MutationResult(
                        success=False,
                        message=f"Role '{name}' already exists",
                    )
                role.name = name
            if description is not None:
                role.description = description
            role.save()
            return MutationResult(success=True, message="Role updated", id=id)
        except Exception as e:
            logger.error(f"Error updating role: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Toggle a role active/inactive")
    @require_admin
    def toggle_role(self, info: Info, id: str, active: bool) -> MutationResult:
        from bson import ObjectId

        from crits.core.role import Role

        try:
            role = Role.objects(id=ObjectId(id)).first()
            if not role:
                return MutationResult(success=False, message="Role not found")

            role.active = "on" if active else "off"
            role.save()
            return MutationResult(
                success=True,
                message=f"Role '{role.name}' {'activated' if active else 'deactivated'}",
                id=id,
            )
        except Exception as e:
            logger.error(f"Error toggling role: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Add a source to a role with access flags")
    @require_admin
    def add_role_source(
        self,
        info: Info,
        id: str,
        source_name: str,
        read: bool = False,
        write: bool = False,
        tlp_red: bool = False,
        tlp_amber: bool = False,
        tlp_green: bool = False,
    ) -> MutationResult:
        from bson import ObjectId

        from crits.core.role import Role

        try:
            role = Role.objects(id=ObjectId(id)).first()
            if not role:
                return MutationResult(success=False, message="Role not found")

            role.add_source(
                source_name,
                read=read,
                write=write,
                tlp_red=tlp_red,
                tlp_amber=tlp_amber,
                tlp_green=tlp_green,
            )
            role.save()
            return MutationResult(
                success=True,
                message=f"Source '{source_name}' added to role",
                id=id,
            )
        except Exception as e:
            logger.error(f"Error adding role source: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Remove a source from a role")
    @require_admin
    def remove_role_source(self, info: Info, id: str, source_name: str) -> MutationResult:
        from bson import ObjectId

        from crits.core.role import Role

        try:
            role = Role.objects(id=ObjectId(id)).first()
            if not role:
                return MutationResult(success=False, message="Role not found")

            role.sources = [s for s in role.sources if s.name != source_name]
            role.save()
            return MutationResult(
                success=True,
                message=f"Source '{source_name}' removed from role",
                id=id,
            )
        except Exception as e:
            logger.error(f"Error removing role source: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Set a boolean permission on a role")
    @require_admin
    def set_role_permission(
        self, info: Info, id: str, permission: str, value: bool
    ) -> MutationResult:
        from bson import ObjectId

        from crits.core.role import Role

        try:
            role = Role.objects(id=ObjectId(id)).first()
            if not role:
                return MutationResult(success=False, message="Role not found")

            if not hasattr(role, permission):
                return MutationResult(
                    success=False,
                    message=f"Unknown permission: {permission}",
                )

            setattr(role, permission, value)
            role.save()
            return MutationResult(
                success=True,
                message=f"Permission '{permission}' set to {value}",
                id=id,
            )
        except Exception as e:
            logger.error(f"Error setting role permission: {e}")
            return MutationResult(success=False, message=str(e))

    # ── Generic config items ─────────────────────────────────────────

    @strawberry.mutation(description="Create a config item (raw data type, signature type, etc.)")
    @require_admin
    def create_config_item(
        self, info: Info, config_type: ConfigTypeEnum, name: str
    ) -> MutationResult:
        try:
            model = _get_config_model(config_type)
            existing = model.objects(name=name).first()
            if existing:
                return MutationResult(
                    success=False,
                    message=f"'{name}' already exists for {config_type.value}",
                )

            item = model(name=name, active="on")
            item.save()
            return MutationResult(
                success=True,
                message=f"'{name}' created",
                id=str(item.id),
            )
        except Exception as e:
            logger.error(f"Error creating config item: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Toggle a config item active/inactive")
    @require_admin
    def toggle_config_item(
        self, info: Info, config_type: ConfigTypeEnum, name: str, active: bool
    ) -> MutationResult:
        try:
            model = _get_config_model(config_type)
            item = model.objects(name=name).first()
            if not item:
                return MutationResult(
                    success=False,
                    message=f"'{name}' not found for {config_type.value}",
                )

            item.active = "on" if active else "off"
            item.save()
            return MutationResult(
                success=True,
                message=f"'{name}' {'activated' if active else 'deactivated'}",
            )
        except Exception as e:
            logger.error(f"Error toggling config item: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Delete a config item")
    @require_admin
    def delete_config_item(
        self, info: Info, config_type: ConfigTypeEnum, name: str
    ) -> DeleteResult:
        try:
            model = _get_config_model(config_type)
            item = model.objects(name=name).first()
            if not item:
                return DeleteResult(
                    success=False,
                    message=f"'{name}' not found for {config_type.value}",
                )

            item_id = str(item.id)
            item.delete()
            return DeleteResult(
                success=True,
                message=f"'{name}' deleted",
                deleted_id=item_id,
            )
        except Exception as e:
            logger.error(f"Error deleting config item: {e}")
            return DeleteResult(success=False, message=str(e))
