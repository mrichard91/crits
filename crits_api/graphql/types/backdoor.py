"""
Backdoor GraphQL type for CRITs API.
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
class BackdoorType:
    """
    CRITs Backdoor - represents a backdoor or malware family.

    Backdoors are named malware families or tools used by threat actors.
    """

    id: str
    name: str
    description: str = ""
    aliases: list[str] = strawberry.field(default_factory=list)
    version: str = ""
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
    def from_model(cls, backdoor: Any) -> "BackdoorType":
        """Create BackdoorType from Backdoor MongoEngine model."""
        return cls(
            id=str(backdoor.id),
            name=getattr(backdoor, "name", "") or "",
            description=getattr(backdoor, "description", "") or "",
            aliases=list(getattr(backdoor, "aliases", []) or []),
            version=getattr(backdoor, "version", "") or "",
            analyst=getattr(backdoor, "analyst", "") or "",
            status=getattr(backdoor, "status", "") or "",
            tlp=getattr(backdoor, "tlp", "") or "",
            created=getattr(backdoor, "created", None),
            modified=getattr(backdoor, "modified", None),
            campaigns=extract_campaigns(backdoor),
            bucket_list=list(getattr(backdoor, "bucket_list", []) or []),
            sectors=list(getattr(backdoor, "sectors", []) or []),
            sources=extract_sources(backdoor),
            relationships=extract_relationships(backdoor),
            actions=extract_actions(backdoor),
            tickets=extract_tickets(backdoor),
        )
