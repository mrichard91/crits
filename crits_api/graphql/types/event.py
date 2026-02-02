"""
Event GraphQL type for CRITs API.
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
class EventType:
    """
    CRITs Event - represents a security event or incident.

    Events group related threat indicators and provide context for incidents.
    """

    id: str
    title: str
    event_type: str
    event_id: str = ""
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
    def from_model(cls, event) -> "EventType":
        """Create EventType from Event MongoEngine model."""
        # Handle event_id which is a UUID field
        event_id = ''
        if hasattr(event, 'event_id') and event.event_id:
            event_id = str(event.event_id)

        return cls(
            id=str(event.id),
            title=getattr(event, 'title', '') or '',
            event_type=getattr(event, 'event_type', '') or '',
            event_id=event_id,
            description=getattr(event, 'description', '') or '',
            analyst=getattr(event, 'analyst', '') or '',
            status=getattr(event, 'status', '') or '',
            tlp=getattr(event, 'tlp', '') or '',
            created=getattr(event, 'created', None),
            modified=getattr(event, 'modified', None),
            campaigns=extract_campaigns(event),
            bucket_list=list(getattr(event, 'bucket_list', []) or []),
            sectors=list(getattr(event, 'sectors', []) or []),
            sources=extract_sources(event),
            relationships=extract_relationships(event),
            actions=extract_actions(event),
            tickets=extract_tickets(event),
        )
