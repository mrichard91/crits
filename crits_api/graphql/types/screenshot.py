"""
Screenshot GraphQL type for CRITs API.
"""

from datetime import datetime
from typing import Any

import strawberry

from crits_api.graphql.types.common import (
    SourceInfo,
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
    tags: list[str] = strawberry.field(default_factory=list)
    created: datetime | None = None
    modified: datetime | None = None

    # Relationships and metadata
    sources: list[SourceInfo] = strawberry.field(default_factory=list)

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
            tags=list(getattr(screenshot, "tags", []) or []),
            created=getattr(screenshot, "created", None),
            modified=getattr(screenshot, "modified", None),
            sources=extract_sources(screenshot),
        )
