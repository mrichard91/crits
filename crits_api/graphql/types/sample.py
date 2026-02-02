"""
Sample GraphQL type for CRITs API.
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
class SampleType:
    """
    CRITs Sample - represents a malware sample or file.

    Samples are files (typically malware) with associated metadata and hashes.
    """

    id: str
    filename: str
    filenames: list[str] = strawberry.field(default_factory=list)
    filetype: str = ""
    mimetype: str = ""
    size: int = 0

    # Hash values
    md5: str = ""
    sha1: str = ""
    sha256: str = ""
    ssdeep: str = ""
    impfuzzy: str = ""

    # Common fields
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
    def from_model(cls, sample) -> "SampleType":
        """Create SampleType from Sample MongoEngine model."""
        return cls(
            id=str(sample.id),
            filename=getattr(sample, 'filename', '') or '',
            filenames=list(getattr(sample, 'filenames', []) or []),
            filetype=getattr(sample, 'filetype', '') or '',
            mimetype=getattr(sample, 'mimetype', '') or '',
            size=getattr(sample, 'size', 0) or 0,
            md5=getattr(sample, 'md5', '') or '',
            sha1=getattr(sample, 'sha1', '') or '',
            sha256=getattr(sample, 'sha256', '') or '',
            ssdeep=getattr(sample, 'ssdeep', '') or '',
            impfuzzy=getattr(sample, 'impfuzzy', '') or '',
            description=getattr(sample, 'description', '') or '',
            analyst=getattr(sample, 'analyst', '') or '',
            status=getattr(sample, 'status', '') or '',
            tlp=getattr(sample, 'tlp', '') or '',
            created=getattr(sample, 'created', None),
            modified=getattr(sample, 'modified', None),
            campaigns=extract_campaigns(sample),
            bucket_list=list(getattr(sample, 'bucket_list', []) or []),
            sectors=list(getattr(sample, 'sectors', []) or []),
            sources=extract_sources(sample),
            relationships=extract_relationships(sample),
            actions=extract_actions(sample),
            tickets=extract_tickets(sample),
        )
