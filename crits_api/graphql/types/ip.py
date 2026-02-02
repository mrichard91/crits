"""
IP GraphQL type for CRITs API.
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
class IPType:
    """
    CRITs IP - represents an IP address indicator.

    IPs are network addresses associated with malicious activity.
    """

    id: str
    ip: str
    ip_type: str = ""
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
    def from_model(cls, ip_obj) -> "IPType":
        """Create IPType from IP MongoEngine model."""
        return cls(
            id=str(ip_obj.id),
            ip=getattr(ip_obj, 'ip', '') or '',
            ip_type=getattr(ip_obj, 'ip_type', '') or '',
            description=getattr(ip_obj, 'description', '') or '',
            analyst=getattr(ip_obj, 'analyst', '') or '',
            status=getattr(ip_obj, 'status', '') or '',
            tlp=getattr(ip_obj, 'tlp', '') or '',
            created=getattr(ip_obj, 'created', None),
            modified=getattr(ip_obj, 'modified', None),
            campaigns=extract_campaigns(ip_obj),
            bucket_list=list(getattr(ip_obj, 'bucket_list', []) or []),
            sectors=list(getattr(ip_obj, 'sectors', []) or []),
            sources=extract_sources(ip_obj),
            relationships=extract_relationships(ip_obj),
            actions=extract_actions(ip_obj),
            tickets=extract_tickets(ip_obj),
        )
