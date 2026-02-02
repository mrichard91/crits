"""
RawData GraphQL type for CRITs API.
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
class EmbeddedToolType:
    """Tool information for raw data."""

    name: str = ""
    version: str = ""
    details: str = ""

    @classmethod
    def from_model(cls, tool: Any) -> "EmbeddedToolType":
        """Create from EmbeddedTool model."""
        return cls(
            name=getattr(tool, "name", "") or "",
            version=getattr(tool, "version", "") or "",
            details=getattr(tool, "details", "") or "",
        )


@strawberry.type
class EmbeddedHighlightType:
    """Highlighted line with comment."""

    line: int = 0
    line_data: str = ""
    comment: str = ""
    analyst: str = ""
    date: datetime | None = None
    line_date: datetime | None = None

    @classmethod
    def from_model(cls, highlight: Any) -> "EmbeddedHighlightType":
        """Create from EmbeddedHighlight model."""
        return cls(
            line=getattr(highlight, "line", 0) or 0,
            line_data=getattr(highlight, "line_data", "") or "",
            comment=getattr(highlight, "comment", "") or "",
            analyst=getattr(highlight, "analyst", "") or "",
            date=getattr(highlight, "date", None),
            line_date=getattr(highlight, "line_date", None),
        )


@strawberry.type
class EmbeddedInlineType:
    """Inline comment."""

    line: int = 0
    comment: str = ""
    analyst: str = ""
    date: datetime | None = None
    counter: int = 0

    @classmethod
    def from_model(cls, inline: Any) -> "EmbeddedInlineType":
        """Create from EmbeddedInline model."""
        return cls(
            line=getattr(inline, "line", 0) or 0,
            comment=getattr(inline, "comment", "") or "",
            analyst=getattr(inline, "analyst", "") or "",
            date=getattr(inline, "date", None),
            counter=getattr(inline, "counter", 0) or 0,
        )


@strawberry.type
class RawDataType:
    """
    CRITs RawData - represents raw data like logs or text.

    RawData stores arbitrary text data with optional highlighting and annotations.
    """

    id: str
    title: str = ""
    data_type: str = ""
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

    # Raw data specific
    tool: EmbeddedToolType | None = None
    highlights: list[EmbeddedHighlightType] = strawberry.field(default_factory=list)
    inlines: list[EmbeddedInlineType] = strawberry.field(default_factory=list)

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
    def from_model(cls, raw_data: Any) -> "RawDataType":
        """Create RawDataType from RawData MongoEngine model."""
        # Handle tool
        tool = None
        if hasattr(raw_data, "tool") and raw_data.tool:
            tool = EmbeddedToolType.from_model(raw_data.tool)

        # Handle highlights
        highlights = []
        if hasattr(raw_data, "highlights") and raw_data.highlights:
            for h in raw_data.highlights:
                highlights.append(EmbeddedHighlightType.from_model(h))

        # Handle inlines
        inlines = []
        if hasattr(raw_data, "inlines") and raw_data.inlines:
            for i in raw_data.inlines:
                inlines.append(EmbeddedInlineType.from_model(i))

        # Handle link_id UUID
        link_id = ""
        if hasattr(raw_data, "link_id") and raw_data.link_id:
            link_id = str(raw_data.link_id)

        return cls(
            id=str(raw_data.id),
            title=getattr(raw_data, "title", "") or "",
            data_type=getattr(raw_data, "data_type", "") or "",
            data=getattr(raw_data, "data", "") or "",
            md5=getattr(raw_data, "md5", "") or "",
            link_id=link_id,
            version=getattr(raw_data, "version", 0) or 0,
            description=getattr(raw_data, "description", "") or "",
            analyst=getattr(raw_data, "analyst", "") or "",
            status=getattr(raw_data, "status", "") or "",
            tlp=getattr(raw_data, "tlp", "") or "",
            created=getattr(raw_data, "created", None),
            modified=getattr(raw_data, "modified", None),
            tool=tool,
            highlights=highlights,
            inlines=inlines,
            campaigns=extract_campaigns(raw_data),
            bucket_list=list(getattr(raw_data, "bucket_list", []) or []),
            sectors=list(getattr(raw_data, "sectors", []) or []),
            sources=extract_sources(raw_data),
            relationships=extract_relationships(raw_data),
            actions=extract_actions(raw_data),
            tickets=extract_tickets(raw_data),
        )
