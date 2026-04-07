"""
Admin configuration queries for CRITs GraphQL API.

Provides read access to sources, roles, config types, and vocabularies.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_admin, require_authenticated
from crits_api.db.admin_access_records import (
    get_role_record,
    list_role_records,
    list_source_access_records,
)
from crits_api.db.admin_config_records import (
    AdminConfigType,
    list_admin_config_records,
)
from crits_api.db.admin_user_records import get_user_record, list_user_records
from crits_api.db.tlo_vocabulary import (
    DEFAULT_EVENT_TYPES,
    DEFAULT_OBJECT_TYPES,
    DEFAULT_RELATIONSHIP_TYPES,
    DEFAULT_SECTORS,
)
from crits_api.graphql.types.admin import (
    NamedConfigType,
    RoleType,
    SourceAccessType,
)
from crits_api.graphql.types.user import UserType

logger = logging.getLogger(__name__)


@strawberry.type
class AdminQueries:
    """Admin configuration queries."""

    @strawberry.field(description="List all sources")
    @require_admin
    def sources(self, info: Info) -> list[SourceAccessType]:
        try:
            return [SourceAccessType.from_model(source) for source in list_source_access_records()]
        except Exception as e:
            logger.error(f"Error fetching sources: {e}")
            return []

    @strawberry.field(description="List all roles")
    @require_admin
    def roles(self, info: Info) -> list[RoleType]:
        try:
            return [RoleType.from_model(role) for role in list_role_records()]
        except Exception as e:
            logger.error(f"Error fetching roles: {e}")
            return []

    @strawberry.field(description="Get a single role by ID")
    @require_admin
    def role(self, info: Info, id: str) -> RoleType | None:
        try:
            role = get_role_record(id)
            if role:
                return RoleType.from_model(role)
            return None
        except Exception as e:
            logger.error(f"Error fetching role {id}: {e}")
            return None

    @strawberry.field(description="List all users")
    @require_admin
    def users(self, info: Info) -> list[UserType]:
        try:
            return [UserType.from_model(user) for user in list_user_records()]
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []

    @strawberry.field(description="Get a single user by ID")
    @require_admin
    def user(self, info: Info, id: str) -> UserType | None:
        try:
            user = get_user_record(id)
            if user:
                return UserType.from_model(user)
            return None
        except Exception as e:
            logger.error(f"Error fetching user {id}: {e}")
            return None

    @strawberry.field(description="List raw data types")
    @require_admin
    def raw_data_types(self, info: Info) -> list[NamedConfigType]:
        try:
            return [
                NamedConfigType.from_model(record)
                for record in list_admin_config_records(AdminConfigType.RAW_DATA_TYPE)
            ]
        except Exception as e:
            logger.error(f"Error fetching raw data types: {e}")
            return []

    @strawberry.field(description="List signature types")
    @require_admin
    def signature_types(self, info: Info) -> list[NamedConfigType]:
        try:
            return [
                NamedConfigType.from_model(record)
                for record in list_admin_config_records(AdminConfigType.SIGNATURE_TYPE)
            ]
        except Exception as e:
            logger.error(f"Error fetching signature types: {e}")
            return []

    @strawberry.field(description="List signature dependencies")
    @require_admin
    def signature_dependencies(self, info: Info) -> list[NamedConfigType]:
        try:
            return [
                NamedConfigType.from_model(record)
                for record in list_admin_config_records(AdminConfigType.SIGNATURE_DEPENDENCY)
            ]
        except Exception as e:
            logger.error(f"Error fetching signature dependencies: {e}")
            return []

    @strawberry.field(description="List IDB actions")
    @require_admin
    def actions(self, info: Info) -> list[NamedConfigType]:
        try:
            return [
                NamedConfigType.from_model(record)
                for record in list_admin_config_records(AdminConfigType.ACTION)
            ]
        except Exception as e:
            logger.error(f"Error fetching actions: {e}")
            return []

    @strawberry.field(description="Get event type vocabulary (read-only)")
    @require_authenticated
    def event_type_vocabulary(self, info: Info) -> list[str]:
        return sorted(DEFAULT_EVENT_TYPES)

    @strawberry.field(description="Get relationship type vocabulary (read-only)")
    @require_authenticated
    def relationship_type_vocabulary(self, info: Info) -> list[str]:
        return sorted(DEFAULT_RELATIONSHIP_TYPES)

    @strawberry.field(description="Get object type vocabulary (read-only)")
    @require_authenticated
    def object_type_vocabulary(self, info: Info) -> list[str]:
        return sorted(DEFAULT_OBJECT_TYPES)

    @strawberry.field(description="Get sector vocabulary (read-only)")
    @require_authenticated
    def sector_vocabulary(self, info: Info) -> list[str]:
        return sorted(DEFAULT_SECTORS)
