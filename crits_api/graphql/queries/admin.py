"""
Admin configuration queries for CRITs GraphQL API.

Provides read access to sources, roles, config types, and vocabularies.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_admin, require_authenticated
from crits_api.db.admin_config_records import (
    AdminConfigType,
    list_admin_config_records,
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
        from crits.core.source_access import SourceAccess

        try:
            return [SourceAccessType.from_model(s) for s in SourceAccess.objects().order_by("name")]
        except Exception as e:
            logger.error(f"Error fetching sources: {e}")
            return []

    @strawberry.field(description="List all roles")
    @require_admin
    def roles(self, info: Info) -> list[RoleType]:
        from crits.core.role import Role

        try:
            return [RoleType.from_model(r) for r in Role.objects().order_by("name")]
        except Exception as e:
            logger.error(f"Error fetching roles: {e}")
            return []

    @strawberry.field(description="Get a single role by ID")
    @require_admin
    def role(self, info: Info, id: str) -> RoleType | None:
        from bson import ObjectId

        from crits.core.role import Role

        try:
            role = Role.objects(id=ObjectId(id)).first()
            if role:
                return RoleType.from_model(role)
            return None
        except Exception as e:
            logger.error(f"Error fetching role {id}: {e}")
            return None

    @strawberry.field(description="List all users")
    @require_admin
    def users(self, info: Info) -> list[UserType]:
        from crits.core.user import CRITsUser

        try:
            return [
                UserType.from_model(u)
                for u in CRITsUser.objects().order_by("username").exclude("subscriptions")
            ]
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []

    @strawberry.field(description="Get a single user by ID")
    @require_admin
    def user(self, info: Info, id: str) -> UserType | None:
        from bson import ObjectId

        from crits.core.user import CRITsUser

        try:
            user = CRITsUser.objects(id=ObjectId(id)).exclude("subscriptions").first()
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
        from crits.vocabulary.events import EventTypes

        return EventTypes.values(sort=True)

    @strawberry.field(description="Get relationship type vocabulary (read-only)")
    @require_authenticated
    def relationship_type_vocabulary(self, info: Info) -> list[str]:
        from crits.vocabulary.relationships import RelationshipTypes

        return RelationshipTypes.values(sort=True)

    @strawberry.field(description="Get object type vocabulary (read-only)")
    @require_authenticated
    def object_type_vocabulary(self, info: Info) -> list[str]:
        from crits.vocabulary.objects import ObjectTypes

        return ObjectTypes.values(sort=True)

    @strawberry.field(description="Get sector vocabulary (read-only)")
    @require_authenticated
    def sector_vocabulary(self, info: Info) -> list[str]:
        from crits.vocabulary.sectors import Sectors

        return Sectors.values(sort=True)
