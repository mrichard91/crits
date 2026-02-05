"""
Screenshot GraphQL type for CRITs API.
"""

from datetime import datetime
from typing import Any

import strawberry

from crits_api.graphql.types.common import (
    EmbeddedRelationshipType,
    SourceInfo,
    extract_campaigns,
    extract_relationships,
    extract_sources,
)


@strawberry.type
class ScreenshotType:
    """
    CRITs Screenshot - represents a screenshot image.

    Screenshots are images captured from malware analysis or web pages.
    """

    id: str
    filename: str = ""
    description: str = ""
    md5: str = ""
    width: int = 0
    height: int = 0
    analyst: str = ""
    status: str = ""
    tlp: str = ""
    tags: list[str] = strawberry.field(default_factory=list)
    created: datetime | None = None
    modified: datetime | None = None

    # Common TLO fields
    campaigns: list[str] = strawberry.field(default_factory=list)
    bucket_list: list[str] = strawberry.field(default_factory=list)
    sectors: list[str] = strawberry.field(default_factory=list)

    # Relationships and metadata
    sources: list[SourceInfo] = strawberry.field(default_factory=list)
    relationships: list[EmbeddedRelationshipType] = strawberry.field(default_factory=list)

    @classmethod
    def from_model(cls, screenshot: Any) -> "ScreenshotType":
        """Create ScreenshotType from Screenshot MongoEngine model."""
        return cls(
            id=str(screenshot.id),
            filename=getattr(screenshot, "filename", "") or "",
            description=getattr(screenshot, "description", "") or "",
            md5=getattr(screenshot, "md5", "") or "",
            width=getattr(screenshot, "width", 0) or 0,
            height=getattr(screenshot, "height", 0) or 0,
            analyst=getattr(screenshot, "analyst", "") or "",
            status=getattr(screenshot, "status", "") or "",
            tlp=getattr(screenshot, "tlp", "") or "",
            tags=list(getattr(screenshot, "tags", []) or []),
            created=getattr(screenshot, "created", None),
            modified=getattr(screenshot, "modified", None),
            campaigns=extract_campaigns(screenshot),
            bucket_list=list(getattr(screenshot, "bucket_list", []) or []),
            sectors=list(getattr(screenshot, "sectors", []) or []),
            sources=extract_sources(screenshot),
            relationships=extract_relationships(screenshot),
        )
