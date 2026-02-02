"""
Certificate GraphQL type for CRITs API.
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
class CertificateType:
    """
    CRITs Certificate - represents a digital certificate.

    Certificates are X.509 or other digital certificates found in malware or infrastructure.
    """

    id: str
    filename: str
    filetype: str = ""
    md5: str = ""
    size: int = 0
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
    def from_model(cls, cert) -> "CertificateType":
        """Create CertificateType from Certificate MongoEngine model."""
        return cls(
            id=str(cert.id),
            filename=getattr(cert, 'filename', '') or '',
            filetype=getattr(cert, 'filetype', '') or '',
            md5=getattr(cert, 'md5', '') or '',
            size=getattr(cert, 'size', 0) or 0,
            description=getattr(cert, 'description', '') or '',
            analyst=getattr(cert, 'analyst', '') or '',
            status=getattr(cert, 'status', '') or '',
            tlp=getattr(cert, 'tlp', '') or '',
            created=getattr(cert, 'created', None),
            modified=getattr(cert, 'modified', None),
            campaigns=extract_campaigns(cert),
            bucket_list=list(getattr(cert, 'bucket_list', []) or []),
            sectors=list(getattr(cert, 'sectors', []) or []),
            sources=extract_sources(cert),
            relationships=extract_relationships(cert),
            actions=extract_actions(cert),
            tickets=extract_tickets(cert),
        )
