"""
Target GraphQL type for CRITs API.
"""

from datetime import datetime
from typing import Any

import strawberry

from crits_api.graphql.types.common import (
    EmbeddedActionType,
    EmbeddedRelationshipType,
    EmbeddedTicketType,
    SourceInfo,
    extract_actions,
    extract_campaigns,
    extract_relationships,
    extract_sources,
    extract_tickets,
)


@strawberry.type
class TargetType:
    """
    CRITs Target - represents a targeted individual or organization.

    Targets are people or entities that have been targeted by threat actors.
    """

    id: str
    email_address: str
    email_count: int = 0
    firstname: str = ""
    lastname: str = ""
    title: str = ""
    department: str = ""
    division: str = ""
    organization_id: str = ""
    note: str = ""
    description: str = ""
    analyst: str = ""
    status: str = ""
    tlp: str = ""
    created: datetime | None = None
    modified: datetime | None = None

    # Common TLO fields
    campaigns: list[str] = strawberry.field(default_factory=list)
    bucket_list: list[str] = strawberry.field(default_factory=list)
    sectors: list[str] = strawberry.field(default_factory=list)

    # Relationships and metadata
    sources: list[SourceInfo] = strawberry.field(default_factory=list)
    relationships: list[EmbeddedRelationshipType] = strawberry.field(default_factory=list)
    actions: list[EmbeddedActionType] = strawberry.field(default_factory=list)
    tickets: list[EmbeddedTicketType] = strawberry.field(default_factory=list)

    @classmethod
    def from_model(cls, target: Any) -> "TargetType":
        """Create TargetType from Target MongoEngine model."""
        return cls(
            id=str(target.id),
            email_address=getattr(target, "email_address", "") or "",
            email_count=getattr(target, "email_count", 0) or 0,
            firstname=getattr(target, "firstname", "") or "",
            lastname=getattr(target, "lastname", "") or "",
            title=getattr(target, "title", "") or "",
            department=getattr(target, "department", "") or "",
            division=getattr(target, "division", "") or "",
            organization_id=getattr(target, "organization_id", "") or "",
            note=getattr(target, "note", "") or "",
            description=getattr(target, "description", "") or "",
            analyst=getattr(target, "analyst", "") or "",
            status=getattr(target, "status", "") or "",
            tlp=getattr(target, "tlp", "") or "",
            created=getattr(target, "created", None),
            modified=getattr(target, "modified", None),
            campaigns=extract_campaigns(target),
            bucket_list=list(getattr(target, "bucket_list", []) or []),
            sectors=list(getattr(target, "sectors", []) or []),
            sources=extract_sources(target),
            relationships=extract_relationships(target),
            actions=extract_actions(target),
            tickets=extract_tickets(target),
        )
