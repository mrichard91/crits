"""
Email GraphQL type for CRITs API.

Named email_type.py to avoid collision with Python's email module.
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
class EmailType:
    """
    CRITs Email - represents an email message.

    Emails are phishing or malicious email messages with headers and content.
    """

    id: str
    subject: str = ""
    from_address: str = ""
    sender: str = ""
    reply_to: str = ""
    to: list[str] = strawberry.field(default_factory=list)
    cc: list[str] = strawberry.field(default_factory=list)
    date: str = ""
    isodate: datetime | None = None
    message_id: str = ""
    originating_ip: str = ""
    x_originating_ip: str = ""
    x_mailer: str = ""
    helo: str = ""
    boundary: str = ""
    raw_body: str = ""
    raw_header: str = ""
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
    def from_model(cls, email: Any) -> "EmailType":
        """Create EmailType from Email MongoEngine model."""
        # Handle raw_header which may be a special field type
        raw_header = ""
        if hasattr(email, "raw_header"):
            rh = email.raw_header
            if rh:
                raw_header = str(rh) if not isinstance(rh, str) else rh

        return cls(
            id=str(email.id),
            subject=getattr(email, "subject", "") or "",
            from_address=getattr(email, "from_address", "") or "",
            sender=getattr(email, "sender", "") or "",
            reply_to=getattr(email, "reply_to", "") or "",
            to=list(getattr(email, "to", []) or []),
            cc=list(getattr(email, "cc", []) or []),
            date=getattr(email, "date", "") or "",
            isodate=getattr(email, "isodate", None),
            message_id=getattr(email, "message_id", "") or "",
            originating_ip=getattr(email, "originating_ip", "") or "",
            x_originating_ip=getattr(email, "x_originating_ip", "") or "",
            x_mailer=getattr(email, "x_mailer", "") or "",
            helo=getattr(email, "helo", "") or "",
            boundary=getattr(email, "boundary", "") or "",
            raw_body=getattr(email, "raw_body", "") or "",
            raw_header=raw_header,
            description=getattr(email, "description", "") or "",
            analyst=getattr(email, "analyst", "") or "",
            status=getattr(email, "status", "") or "",
            tlp=getattr(email, "tlp", "") or "",
            created=getattr(email, "created", None),
            modified=getattr(email, "modified", None),
            campaigns=extract_campaigns(email),
            bucket_list=list(getattr(email, "bucket_list", []) or []),
            sectors=list(getattr(email, "sectors", []) or []),
            sources=extract_sources(email),
            relationships=extract_relationships(email),
            actions=extract_actions(email),
            tickets=extract_tickets(email),
        )
