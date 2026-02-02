"""
Campaign GraphQL type for CRITs API.
"""

from datetime import datetime

import strawberry

from crits_api.graphql.types.common import (
    extract_relationships,
    extract_actions,
    extract_tickets,
    EmbeddedRelationshipType,
    EmbeddedActionType,
    EmbeddedTicketType,
)


@strawberry.type
class EmbeddedTTPType:
    """Tactics, Techniques, and Procedures."""

    ttp: str = ""
    analyst: str = ""
    date: datetime | None = None

    @classmethod
    def from_model(cls, ttp) -> "EmbeddedTTPType":
        """Create from EmbeddedTTP model."""
        return cls(
            ttp=getattr(ttp, 'ttp', '') or '',
            analyst=getattr(ttp, 'analyst', '') or '',
            date=getattr(ttp, 'date', None),
        )


@strawberry.type
class CampaignType:
    """
    CRITs Campaign - represents a threat campaign.

    Campaigns group related threat activity and associated TLOs.
    """

    id: str
    name: str
    description: str = ""
    aliases: list[str] = strawberry.field(default_factory=list)
    active: str = ""
    analyst: str = ""
    status: str = ""
    tlp: str = ""
    created: datetime | None = None
    modified: datetime | None = None

    # TTPs
    ttps: list[EmbeddedTTPType] = strawberry.field(default_factory=list)

    # Counts (from MapReduce)
    actor_count: int = 0
    backdoor_count: int = 0
    domain_count: int = 0
    email_count: int = 0
    event_count: int = 0
    exploit_count: int = 0
    indicator_count: int = 0
    ip_count: int = 0
    pcap_count: int = 0
    sample_count: int = 0

    # Common TLO fields
    bucket_list: list[str] = strawberry.field(default_factory=list)
    sectors: list[str] = strawberry.field(default_factory=list)

    # Relationships and metadata
    relationships: list[EmbeddedRelationshipType] = strawberry.field(default_factory=list)
    actions: list[EmbeddedActionType] = strawberry.field(default_factory=list)
    tickets: list[EmbeddedTicketType] = strawberry.field(default_factory=list)

    @classmethod
    def from_model(cls, campaign) -> "CampaignType":
        """Create CampaignType from Campaign MongoEngine model."""
        # Handle TTPs
        ttps = []
        if hasattr(campaign, 'ttps') and campaign.ttps:
            for ttp in campaign.ttps:
                ttps.append(EmbeddedTTPType.from_model(ttp))

        return cls(
            id=str(campaign.id),
            name=getattr(campaign, 'name', '') or '',
            description=getattr(campaign, 'description', '') or '',
            aliases=list(getattr(campaign, 'aliases', []) or []),
            active=getattr(campaign, 'active', '') or '',
            analyst=getattr(campaign, 'analyst', '') or '',
            status=getattr(campaign, 'status', '') or '',
            tlp=getattr(campaign, 'tlp', '') or '',
            created=getattr(campaign, 'created', None),
            modified=getattr(campaign, 'modified', None),
            ttps=ttps,
            actor_count=getattr(campaign, 'actor_count', 0) or 0,
            backdoor_count=getattr(campaign, 'backdoor_count', 0) or 0,
            domain_count=getattr(campaign, 'domain_count', 0) or 0,
            email_count=getattr(campaign, 'email_count', 0) or 0,
            event_count=getattr(campaign, 'event_count', 0) or 0,
            exploit_count=getattr(campaign, 'exploit_count', 0) or 0,
            indicator_count=getattr(campaign, 'indicator_count', 0) or 0,
            ip_count=getattr(campaign, 'ip_count', 0) or 0,
            pcap_count=getattr(campaign, 'pcap_count', 0) or 0,
            sample_count=getattr(campaign, 'sample_count', 0) or 0,
            bucket_list=list(getattr(campaign, 'bucket_list', []) or []),
            sectors=list(getattr(campaign, 'sectors', []) or []),
            relationships=extract_relationships(campaign),
            actions=extract_actions(campaign),
            tickets=extract_tickets(campaign),
        )
