"""
PCAP GraphQL type for CRITs API.
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
class PCAPType:
    """
    CRITs PCAP - represents a packet capture file.

    PCAPs are network traffic captures for analysis.
    """

    id: str
    filename: str
    content_type: str = ""
    md5: str = ""
    length: int = 0
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
    def from_model(cls, pcap: Any) -> "PCAPType":
        """Create PCAPType from PCAP MongoEngine model."""
        return cls(
            id=str(pcap.id),
            filename=getattr(pcap, "filename", "") or "",
            content_type=getattr(pcap, "contentType", "") or "",
            md5=getattr(pcap, "md5", "") or "",
            length=getattr(pcap, "length", 0) or 0,
            description=getattr(pcap, "description", "") or "",
            analyst=getattr(pcap, "analyst", "") or "",
            status=getattr(pcap, "status", "") or "",
            tlp=getattr(pcap, "tlp", "") or "",
            created=getattr(pcap, "created", None),
            modified=getattr(pcap, "modified", None),
            campaigns=extract_campaigns(pcap),
            bucket_list=list(getattr(pcap, "bucket_list", []) or []),
            sectors=list(getattr(pcap, "sectors", []) or []),
            sources=extract_sources(pcap),
            relationships=extract_relationships(pcap),
            actions=extract_actions(pcap),
            tickets=extract_tickets(pcap),
        )
