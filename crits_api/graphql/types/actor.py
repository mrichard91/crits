"""
Actor GraphQL type for CRITs API.
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
class EmbeddedActorIdentifierType:
    """Actor identifier with attribution details."""

    identifier_id: str = ""
    analyst: str = ""
    confidence: str = ""
    date: datetime | None = None

    @classmethod
    def from_model(cls, identifier: Any) -> "EmbeddedActorIdentifierType":
        """Create from EmbeddedActorIdentifier model."""
        return cls(
            identifier_id=getattr(identifier, "identifier_id", "") or "",
            analyst=getattr(identifier, "analyst", "") or "",
            confidence=getattr(identifier, "confidence", "") or "",
            date=getattr(identifier, "date", None),
        )


@strawberry.type
class ActorType:
    """
    CRITs Actor - represents a threat actor or adversary.

    Actors are attributed entities responsible for malicious activity.
    """

    id: str
    name: str
    description: str = ""
    aliases: list[str] = strawberry.field(default_factory=list)
    analyst: str = ""
    status: str = ""
    tlp: str = ""
    created: datetime | None = None
    modified: datetime | None = None

    # Actor-specific fields
    identifiers: list[EmbeddedActorIdentifierType] = strawberry.field(default_factory=list)
    intended_effects: list[str] = strawberry.field(default_factory=list)
    motivations: list[str] = strawberry.field(default_factory=list)
    sophistications: list[str] = strawberry.field(default_factory=list)
    threat_types: list[str] = strawberry.field(default_factory=list)

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
    def from_model(cls, actor: Any) -> "ActorType":
        """Create ActorType from Actor MongoEngine model."""
        # Handle identifiers
        identifiers = []
        if hasattr(actor, "identifiers") and actor.identifiers:
            for ident in actor.identifiers:
                identifiers.append(EmbeddedActorIdentifierType.from_model(ident))

        return cls(
            id=str(actor.id),
            name=getattr(actor, "name", "") or "",
            description=getattr(actor, "description", "") or "",
            aliases=list(getattr(actor, "aliases", []) or []),
            analyst=getattr(actor, "analyst", "") or "",
            status=getattr(actor, "status", "") or "",
            tlp=getattr(actor, "tlp", "") or "",
            created=getattr(actor, "created", None),
            modified=getattr(actor, "modified", None),
            identifiers=identifiers,
            intended_effects=list(getattr(actor, "intended_effects", []) or []),
            motivations=list(getattr(actor, "motivations", []) or []),
            sophistications=list(getattr(actor, "sophistications", []) or []),
            threat_types=list(getattr(actor, "threat_types", []) or []),
            campaigns=extract_campaigns(actor),
            bucket_list=list(getattr(actor, "bucket_list", []) or []),
            sectors=list(getattr(actor, "sectors", []) or []),
            sources=extract_sources(actor),
            relationships=extract_relationships(actor),
            actions=extract_actions(actor),
            tickets=extract_tickets(actor),
        )
