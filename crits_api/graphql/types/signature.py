"""
Signature GraphQL type for CRITs API.
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
class SignatureType:
    """
    CRITs Signature - represents a detection signature.

    Signatures are YARA rules, Snort rules, or other detection signatures.
    """

    id: str
    title: str = ""
    data_type: str = ""
    data_type_min_version: str = ""
    data_type_max_version: str = ""
    data_type_dependency: list[str] = strawberry.field(default_factory=list)
    data: str = ""
    md5: str = ""
    link_id: str = ""
    version: int = 0
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
    def from_model(cls, sig) -> "SignatureType":
        """Create SignatureType from Signature MongoEngine model."""
        # Handle link_id UUID
        link_id = ''
        if hasattr(sig, 'link_id') and sig.link_id:
            link_id = str(sig.link_id)

        return cls(
            id=str(sig.id),
            title=getattr(sig, 'title', '') or '',
            data_type=getattr(sig, 'data_type', '') or '',
            data_type_min_version=getattr(sig, 'data_type_min_version', '') or '',
            data_type_max_version=getattr(sig, 'data_type_max_version', '') or '',
            data_type_dependency=list(getattr(sig, 'data_type_dependency', []) or []),
            data=getattr(sig, 'data', '') or '',
            md5=getattr(sig, 'md5', '') or '',
            link_id=link_id,
            version=getattr(sig, 'version', 0) or 0,
            description=getattr(sig, 'description', '') or '',
            analyst=getattr(sig, 'analyst', '') or '',
            status=getattr(sig, 'status', '') or '',
            tlp=getattr(sig, 'tlp', '') or '',
            created=getattr(sig, 'created', None),
            modified=getattr(sig, 'modified', None),
            campaigns=extract_campaigns(sig),
            bucket_list=list(getattr(sig, 'bucket_list', []) or []),
            sectors=list(getattr(sig, 'sectors', []) or []),
            sources=extract_sources(sig),
            relationships=extract_relationships(sig),
            actions=extract_actions(sig),
            tickets=extract_tickets(sig),
        )
