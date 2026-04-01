"""
Admin configuration mutations for CRITs GraphQL API.

CRUD mutations for sources, roles, and simple config types.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_admin
from crits_api.db.admin_access_records import (
    create_role_record,
    create_source_access_record,
    get_role_record_by_name,
    get_source_access_record,
    is_valid_role_permission,
    remove_role_source,
    role_name_exists,
    update_role_permission,
    update_role_record,
    update_source_access_active,
    upsert_role_source,
)
from crits_api.db.admin_config_records import (
    AdminConfigType,
    create_admin_config_record,
    delete_admin_config_record,
    get_admin_config_record,
    update_admin_config_record_active,
)
from crits_api.db.admin_user_records import (
    create_user_record,
    username_exists,
)
from crits_api.db.admin_user_records import (
    reset_user_password as reset_admin_user_password,
)
from crits_api.db.admin_user_records import (
    update_user_record as update_admin_user_record,
)
from crits_api.graphql.types.admin import ConfigTypeEnum
from crits_api.graphql.types.common import DeleteResult, MutationResult

logger = logging.getLogger(__name__)


def _to_admin_config_type(config_type: ConfigTypeEnum) -> AdminConfigType:
    """Translate GraphQL enum values to raw config-record types."""

    return AdminConfigType(config_type.value)


@strawberry.type
class AdminMutations:
    """Admin configuration mutations."""

    # ── Sources ──────────────────────────────────────────────────────

    @strawberry.mutation(description="Create a new source")
    @require_admin
    def create_source(self, info: Info, name: str) -> MutationResult:
        try:
            existing = get_source_access_record(name)
            if existing:
                return MutationResult(success=False, message=f"Source '{name}' already exists")

            source = create_source_access_record(name, active="on")
            return MutationResult(
                success=True,
                message=f"Source '{name}' created",
                id=source.id,
            )
        except Exception as e:
            logger.error(f"Error creating source: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Toggle a source active/inactive")
    @require_admin
    def toggle_source(self, info: Info, name: str, active: bool) -> MutationResult:
        try:
            source = update_source_access_active(name, active=active)
            if not source:
                return MutationResult(success=False, message=f"Source '{name}' not found")

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
        try:
            existing = get_role_record_by_name(name)
            if existing:
                return MutationResult(success=False, message=f"Role '{name}' already exists")

            role = create_role_record(name, description=description or "")
            return MutationResult(
                success=True,
                message=f"Role '{name}' created",
                id=role.id,
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
        try:
            role = update_role_record(id)
            if not role:
                return MutationResult(success=False, message="Role not found")

            if name is not None and role_name_exists(name, exclude_id=id):
                return MutationResult(
                    success=False,
                    message=f"Role '{name}' already exists",
                )
            role = update_role_record(id, name=name, description=description)
            if not role:
                return MutationResult(success=False, message="Role not found")
            return MutationResult(success=True, message="Role updated", id=id)
        except Exception as e:
            logger.error(f"Error updating role: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Toggle a role active/inactive")
    @require_admin
    def toggle_role(self, info: Info, id: str, active: bool) -> MutationResult:
        try:
            role = update_role_record(id, active=active)
            if not role:
                return MutationResult(success=False, message="Role not found")

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
        try:
            role = upsert_role_source(
                id,
                source_name=source_name,
                read=read,
                write=write,
                tlp_red=tlp_red,
                tlp_amber=tlp_amber,
                tlp_green=tlp_green,
            )
            if not role:
                return MutationResult(success=False, message="Role not found")

            return MutationResult(
                success=True,
                message=f"Source '{source_name}' updated on role",
                id=id,
            )
        except Exception as e:
            logger.error(f"Error adding role source: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Remove a source from a role")
    @require_admin
    def remove_role_source(self, info: Info, id: str, source_name: str) -> MutationResult:
        try:
            role = remove_role_source(id, source_name=source_name)
            if not role:
                return MutationResult(success=False, message="Role not found")

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
        try:
            if not is_valid_role_permission(permission):
                return MutationResult(
                    success=False,
                    message=f"Unknown permission: {permission}",
                )

            role = update_role_permission(id, permission=permission, value=value)
            if not role:
                return MutationResult(success=False, message="Role not found")
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
            config_kind = _to_admin_config_type(config_type)
            existing = get_admin_config_record(config_kind, name)
            if existing:
                return MutationResult(
                    success=False,
                    message=f"'{name}' already exists for {config_type.value}",
                )

            item = create_admin_config_record(config_kind, name, active="on")
            return MutationResult(
                success=True,
                message=f"'{name}' created",
                id=item.id,
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
            config_kind = _to_admin_config_type(config_type)
            item = update_admin_config_record_active(config_kind, name, active=active)
            if not item:
                return MutationResult(
                    success=False,
                    message=f"'{name}' not found for {config_type.value}",
                )

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
            config_kind = _to_admin_config_type(config_type)
            item_id = delete_admin_config_record(config_kind, name)
            if not item_id:
                return DeleteResult(
                    success=False,
                    message=f"'{name}' not found for {config_type.value}",
                )

            return DeleteResult(
                success=True,
                message=f"'{name}' deleted",
                deleted_id=item_id,
            )
        except Exception as e:
            logger.error(f"Error deleting config item: {e}")
            return DeleteResult(success=False, message=str(e))

    # ── Users ─────────────────────────────────────────────────────────

    @strawberry.mutation(description="Create a new user")
    @require_admin
    def create_user(
        self,
        info: Info,
        username: str,
        password: str,
        email: str = "",
        first_name: str = "",
        last_name: str = "",
        roles: list[str] | None = None,
    ) -> MutationResult:
        try:
            if username_exists(username):
                return MutationResult(success=False, message=f"User '{username}' already exists")

            user = create_user_record(
                username,
                password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                roles=roles,
            )
            if user is None:
                return MutationResult(
                    success=False,
                    message="Password does not meet complexity requirements",
                )

            return MutationResult(
                success=True,
                message=f"User '{username}' created",
                id=user.id,
            )
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Update a user's profile fields")
    @require_admin
    def update_user(
        self,
        info: Info,
        id: str,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        organization: str | None = None,
    ) -> MutationResult:
        try:
            user = update_admin_user_record(
                id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                organization=organization,
            )
            if not user:
                return MutationResult(success=False, message="User not found")
            return MutationResult(success=True, message="User updated", id=id)
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Toggle a user's active status")
    @require_admin
    def toggle_user_active(self, info: Info, id: str, active: bool) -> MutationResult:
        try:
            user = update_admin_user_record(id, is_active=active)
            if not user:
                return MutationResult(success=False, message="User not found")

            return MutationResult(
                success=True,
                message=f"User '{user.username}' {'activated' if active else 'deactivated'}",
                id=id,
            )
        except Exception as e:
            logger.error(f"Error toggling user active: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Set a user's roles")
    @require_admin
    def set_user_roles(self, info: Info, id: str, roles: list[str]) -> MutationResult:
        try:
            user = update_admin_user_record(id, roles=roles)
            if not user:
                return MutationResult(success=False, message="User not found")
            return MutationResult(success=True, message="Roles updated", id=id)
        except Exception as e:
            logger.error(f"Error setting user roles: {e}")
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation(description="Reset a user's password")
    @require_admin
    def reset_user_password(self, info: Info, id: str, new_password: str) -> MutationResult:
        try:
            user = reset_admin_user_password(id, new_password)
            if user is False:
                return MutationResult(
                    success=False,
                    message="Password does not meet complexity requirements",
                )
            if not user:
                return MutationResult(success=False, message="User not found")
            return MutationResult(success=True, message="Password reset successfully", id=id)
        except Exception as e:
            logger.error(f"Error resetting user password: {e}")
            return MutationResult(success=False, message=str(e))
