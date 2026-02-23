"""
Admin configuration queries for CRITs GraphQL API.

Provides read access to sources, roles, config types, and vocabularies.
"""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_admin, require_authenticated
from crits_api.graphql.types.admin import (
    NamedConfigType,
    RoleType,
    SourceAccessType,
)

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

    @strawberry.field(description="List raw data types")
    @require_admin
    def raw_data_types(self, info: Info) -> list[NamedConfigType]:
        from crits.raw_data.raw_data import RawDataType

        try:
            return [NamedConfigType.from_model(t) for t in RawDataType.objects().order_by("name")]
        except Exception as e:
            logger.error(f"Error fetching raw data types: {e}")
            return []

    @strawberry.field(description="List signature types")
    @require_admin
    def signature_types(self, info: Info) -> list[NamedConfigType]:
        from crits.signatures.signature import SignatureType

        try:
            return [NamedConfigType.from_model(t) for t in SignatureType.objects().order_by("name")]
        except Exception as e:
            logger.error(f"Error fetching signature types: {e}")
            return []

    @strawberry.field(description="List signature dependencies")
    @require_admin
    def signature_dependencies(self, info: Info) -> list[NamedConfigType]:
        from crits.signatures.signature import SignatureDependency

        try:
            return [
                NamedConfigType.from_model(t)
                for t in SignatureDependency.objects().order_by("name")
            ]
        except Exception as e:
            logger.error(f"Error fetching signature dependencies: {e}")
            return []

    @strawberry.field(description="List IDB actions")
    @require_admin
    def actions(self, info: Info) -> list[NamedConfigType]:
        from crits.core.crits_mongoengine import Action

        try:
            return [NamedConfigType.from_model(a) for a in Action.objects().order_by("name")]
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
