"""
Common GraphQL types and scalars for CRITs API.

Includes ObjectID scalar for MongoDB IDs and other shared types.
"""

from datetime import datetime
from enum import Enum
from typing import NewType

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
class SourceInfo:
    """Information about a data source."""

    name: str
    instances: list["SourceInstance"]


@strawberry.type
class SourceInstance:
    """A specific instance of source information."""

    date: datetime
    analyst: str
    method: str = ""
    reference: str = ""
    tlp: TLPLevel = TLPLevel.WHITE


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
