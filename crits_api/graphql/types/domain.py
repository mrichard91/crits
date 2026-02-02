"""
Domain GraphQL type for CRITs API.
"""

from datetime import datetime

import strawberry

from crits_api.graphql.types.common import (
    extract_sources,
    extract_campaigns,
    extract_relationships,
    extract_actions,
    extract_tickets,
    SourceInfo,
    EmbeddedRelationshipType,
    EmbeddedActionType,
    EmbeddedTicketType,
)


@strawberry.type
class DomainType:
    """
    CRITs Domain - represents a domain name indicator.

    Domains are DNS names associated with malicious activity.
    """

    id: str
    domain: str
    record_type: str = ""
    description: str = ""
    analyst: str = ""
    status: str = ""
    tlp: str = ""
    watchlist_enabled: bool = False
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
    def from_model(cls, domain) -> "DomainType":
        """Create DomainType from Domain MongoEngine model."""
        return cls(
            id=str(domain.id),
            domain=getattr(domain, 'domain', '') or '',
            record_type=getattr(domain, 'record_type', '') or '',
            description=getattr(domain, 'description', '') or '',
            analyst=getattr(domain, 'analyst', '') or '',
            status=getattr(domain, 'status', '') or '',
            tlp=getattr(domain, 'tlp', '') or '',
            watchlist_enabled=getattr(domain, 'watchlistEnabled', False) or False,
            created=getattr(domain, 'created', None),
            modified=getattr(domain, 'modified', None),
            campaigns=extract_campaigns(domain),
            bucket_list=list(getattr(domain, 'bucket_list', []) or []),
            sectors=list(getattr(domain, 'sectors', []) or []),
            sources=extract_sources(domain),
            relationships=extract_relationships(domain),
            actions=extract_actions(domain),
            tickets=extract_tickets(domain),
        )
