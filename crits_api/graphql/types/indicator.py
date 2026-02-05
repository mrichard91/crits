"""
Indicator GraphQL type for CRITs API.
"""

from datetime import datetime
from typing import Any

import strawberry

from crits_api.graphql.types.common import (
    EmbeddedRelationshipType,
    SourceInfo,
    extract_relationships,
    extract_sources,
)


@strawberry.type
class ConfidenceType:
    """Confidence rating for an indicator."""

    rating: str = ""
    analyst: str = ""


@strawberry.type
class ImpactType:
    """Impact rating for an indicator."""

    rating: str = ""
    analyst: str = ""


@strawberry.type
class IndicatorType:
    """
    CRITs Indicator - represents an atomic indicator of compromise.

    Examples: IP addresses, domains, email addresses, file hashes, etc.
    """

    id: str
    value: str
    ind_type: str = strawberry.field(description="Indicator type (e.g., IP, Domain, Email)")
    description: str = ""
    analyst: str = ""
    status: str = ""
    tlp: str = ""
    created: datetime | None = None
    modified: datetime | None = None
    confidence: ConfidenceType | None = None
    impact: ImpactType | None = None
    campaigns: list[str] = strawberry.field(default_factory=list)
    threat_types: list[str] = strawberry.field(default_factory=list)
    attack_types: list[str] = strawberry.field(default_factory=list)
    bucket_list: list[str] = strawberry.field(default_factory=list)
    sectors: list[str] = strawberry.field(default_factory=list)

    # Relationships and metadata
    sources: list[SourceInfo] = strawberry.field(default_factory=list)
    relationships: list[EmbeddedRelationshipType] = strawberry.field(default_factory=list)

    @classmethod
    def from_model(cls, indicator: Any) -> "IndicatorType":
        """
        Create IndicatorType from Indicator MongoEngine model.

        Args:
            indicator: Indicator instance

        Returns:
            IndicatorType instance
        """
        # Handle confidence
        confidence = None
        if hasattr(indicator, "confidence") and indicator.confidence:
            confidence = ConfidenceType(
                rating=getattr(indicator.confidence, "rating", "") or "",
                analyst=getattr(indicator.confidence, "analyst", "") or "",
            )

        # Handle impact
        impact = None
        if hasattr(indicator, "impact") and indicator.impact:
            impact = ImpactType(
                rating=getattr(indicator.impact, "rating", "") or "",
                analyst=getattr(indicator.impact, "analyst", "") or "",
            )

        # Handle campaigns (list of embedded docs with name field)
        campaigns = []
        if hasattr(indicator, "campaign") and indicator.campaign:
            for c in indicator.campaign:
                if hasattr(c, "name"):
                    campaigns.append(c.name)

        return cls(
            id=str(indicator.id),
            value=getattr(indicator, "value", "") or "",
            ind_type=getattr(indicator, "ind_type", "") or "",
            description=getattr(indicator, "description", "") or "",
            analyst=getattr(indicator, "analyst", "") or "",
            status=getattr(indicator, "status", "") or "",
            tlp=getattr(indicator, "tlp", "") or "",
            created=getattr(indicator, "created", None),
            modified=getattr(indicator, "modified", None),
            confidence=confidence,
            impact=impact,
            campaigns=campaigns,
            threat_types=list(getattr(indicator, "threat_types", []) or []),
            attack_types=list(getattr(indicator, "attack_types", []) or []),
            bucket_list=list(getattr(indicator, "bucket_list", []) or []),
            sectors=list(getattr(indicator, "sectors", []) or []),
            sources=extract_sources(indicator),
            relationships=extract_relationships(indicator),
        )
