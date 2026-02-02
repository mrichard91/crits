"""
Common GraphQL types and scalars for CRITs API.

Includes ObjectID scalar for MongoDB IDs and other shared types.
"""

from datetime import datetime
from enum import Enum
from typing import Any, NewType

import strawberry
from bson import ObjectId

# Custom scalar for MongoDB ObjectId
ObjectID = strawberry.scalar(
    NewType("ObjectID", str),
    serialize=lambda v: str(v),
    parse_value=lambda v: ObjectId(v) if ObjectId.is_valid(v) else v,
    description="MongoDB ObjectId represented as a string",
)


# DateTime scalar (Strawberry has built-in but we can customize)
DateTime = strawberry.scalar(
    NewType("DateTime", datetime),
    serialize=lambda v: v.isoformat() if v else None,
    parse_value=lambda v: datetime.fromisoformat(v) if v else None,
    description="ISO8601 datetime string",
)


@strawberry.enum
class TLPLevel(Enum):
    """Traffic Light Protocol classification levels."""

    WHITE = "white"
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


@strawberry.enum
class TLOType(Enum):
    """Top-Level Object types in CRITs."""

    ACTOR = "Actor"
    BACKDOOR = "Backdoor"
    CAMPAIGN = "Campaign"
    CERTIFICATE = "Certificate"
    DOMAIN = "Domain"
    EMAIL = "Email"
    EVENT = "Event"
    EXPLOIT = "Exploit"
    INDICATOR = "Indicator"
    IP = "IP"
    PCAP = "PCAP"
    RAW_DATA = "RawData"
    SAMPLE = "Sample"
    SCREENSHOT = "Screenshot"
    SIGNATURE = "Signature"
    TARGET = "Target"


@strawberry.type
class SourceInstance:
    """A specific instance of source information."""

    date: datetime | None = None
    analyst: str = ""
    method: str = ""
    reference: str = ""
    tlp: str = ""


@strawberry.type
class SourceInfo:
    """Information about a data source."""

    name: str
    instances: list[SourceInstance] = strawberry.field(default_factory=list)

    @classmethod
    def from_model(cls, source: Any) -> "SourceInfo":
        """Create SourceInfo from EmbeddedSource model."""
        instances = []
        if hasattr(source, "instances") and source.instances:
            for inst in source.instances:
                instances.append(
                    SourceInstance(
                        date=getattr(inst, "date", None),
                        analyst=getattr(inst, "analyst", "") or "",
                        method=getattr(inst, "method", "") or "",
                        reference=getattr(inst, "reference", "") or "",
                        tlp=getattr(inst, "tlp", "") or "",
                    )
                )
        return cls(
            name=getattr(source, "name", "") or "",
            instances=instances,
        )


@strawberry.type
class EmbeddedCampaignType:
    """Campaign association with confidence level."""

    name: str
    confidence: str = ""
    analyst: str = ""
    date: datetime | None = None

    @classmethod
    def from_model(cls, campaign: Any) -> "EmbeddedCampaignType":
        """Create from EmbeddedCampaign model."""
        return cls(
            name=getattr(campaign, "name", "") or "",
            confidence=getattr(campaign, "confidence", "") or "",
            analyst=getattr(campaign, "analyst", "") or "",
            date=getattr(campaign, "date", None),
        )


@strawberry.type
class EmbeddedRelationshipType:
    """Relationship to another TLO."""

    relationship: str = ""
    rel_type: str = ""
    rel_date: datetime | None = None
    analyst: str = ""
    rel_confidence: str = ""
    rel_reason: str = ""

    @classmethod
    def from_model(cls, rel: Any) -> "EmbeddedRelationshipType":
        """Create from EmbeddedRelationship model."""
        return cls(
            relationship=str(getattr(rel, "relationship", "") or ""),
            rel_type=getattr(rel, "rel_type", "") or "",
            rel_date=getattr(rel, "rel_date", None),
            analyst=getattr(rel, "analyst", "") or "",
            rel_confidence=getattr(rel, "rel_confidence", "") or "",
            rel_reason=getattr(rel, "rel_reason", "") or "",
        )


@strawberry.type
class EmbeddedActionType:
    """Action taken on an object."""

    action_type: str = ""
    analyst: str = ""
    begin_date: datetime | None = None
    end_date: datetime | None = None
    performed_date: datetime | None = None
    active: str = ""
    reason: str = ""
    date: datetime | None = None

    @classmethod
    def from_model(cls, action: Any) -> "EmbeddedActionType":
        """Create from EmbeddedAction model."""
        return cls(
            action_type=getattr(action, "action_type", "") or "",
            analyst=getattr(action, "analyst", "") or "",
            begin_date=getattr(action, "begin_date", None),
            end_date=getattr(action, "end_date", None),
            performed_date=getattr(action, "performed_date", None),
            active=getattr(action, "active", "") or "",
            reason=getattr(action, "reason", "") or "",
            date=getattr(action, "date", None),
        )


@strawberry.type
class EmbeddedTicketType:
    """Ticket reference."""

    ticket_number: str = ""
    analyst: str = ""
    date: datetime | None = None

    @classmethod
    def from_model(cls, ticket: Any) -> "EmbeddedTicketType":
        """Create from EmbeddedTicket model."""
        return cls(
            ticket_number=getattr(ticket, "ticket_number", "") or "",
            analyst=getattr(ticket, "analyst", "") or "",
            date=getattr(ticket, "date", None),
        )


@strawberry.type
class DeleteResult:
    """Result of a delete operation."""

    success: bool
    message: str = ""
    deleted_id: str = ""


@strawberry.type
class BulkResult:
    """Result of a bulk operation."""

    success: bool
    total: int
    succeeded: int
    failed: int
    errors: list[str] = strawberry.field(default_factory=list)


def extract_sources(obj: Any) -> list[SourceInfo]:
    """Extract source list from a CRITs object."""
    sources = []
    if hasattr(obj, "source") and obj.source:
        for src in obj.source:
            sources.append(SourceInfo.from_model(src))
    return sources


def extract_campaigns(obj: Any) -> list[str]:
    """Extract campaign names from a CRITs object."""
    campaigns = []
    if hasattr(obj, "campaign") and obj.campaign:
        for c in obj.campaign:
            if hasattr(c, "name"):
                campaigns.append(c.name)
    return campaigns


def extract_campaign_details(obj: Any) -> list[EmbeddedCampaignType]:
    """Extract full campaign details from a CRITs object."""
    campaigns = []
    if hasattr(obj, "campaign") and obj.campaign:
        for c in obj.campaign:
            campaigns.append(EmbeddedCampaignType.from_model(c))
    return campaigns


def extract_relationships(obj: Any) -> list[EmbeddedRelationshipType]:
    """Extract relationships from a CRITs object."""
    rels = []
    if hasattr(obj, "relationships") and obj.relationships:
        for r in obj.relationships:
            rels.append(EmbeddedRelationshipType.from_model(r))
    return rels


def extract_actions(obj: Any) -> list[EmbeddedActionType]:
    """Extract actions from a CRITs object."""
    actions = []
    if hasattr(obj, "actions") and obj.actions:
        for a in obj.actions:
            actions.append(EmbeddedActionType.from_model(a))
    return actions


def extract_tickets(obj: Any) -> list[EmbeddedTicketType]:
    """Extract tickets from a CRITs object."""
    tickets = []
    if hasattr(obj, "tickets") and obj.tickets:
        for t in obj.tickets:
            tickets.append(EmbeddedTicketType.from_model(t))
    return tickets
