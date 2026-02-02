"""GraphQL type definitions for CRITs API."""

from crits_api.graphql.types.common import (
    ObjectID,
    DateTime,
    TLPLevel,
    TLOType,
    SourceInfo,
    SourceInstance,
    EmbeddedCampaignType,
    EmbeddedRelationshipType,
    EmbeddedActionType,
    EmbeddedTicketType,
    DeleteResult,
    BulkResult,
)
from crits_api.graphql.types.user import UserType
from crits_api.graphql.types.pagination import Connection, PageInfo, Edge

# TLO Types
from crits_api.graphql.types.actor import ActorType
from crits_api.graphql.types.backdoor import BackdoorType
from crits_api.graphql.types.campaign import CampaignType
from crits_api.graphql.types.certificate import CertificateType
from crits_api.graphql.types.domain import DomainType
from crits_api.graphql.types.email_type import EmailType
from crits_api.graphql.types.event import EventType
from crits_api.graphql.types.exploit import ExploitType
from crits_api.graphql.types.indicator import IndicatorType
from crits_api.graphql.types.ip import IPType
from crits_api.graphql.types.pcap import PCAPType
from crits_api.graphql.types.raw_data import RawDataType
from crits_api.graphql.types.sample import SampleType
from crits_api.graphql.types.screenshot import ScreenshotType
from crits_api.graphql.types.signature import SignatureType
from crits_api.graphql.types.target import TargetType

__all__ = [
    # Scalars and enums
    "ObjectID",
    "DateTime",
    "TLPLevel",
    "TLOType",
    # Common types
    "SourceInfo",
    "SourceInstance",
    "EmbeddedCampaignType",
    "EmbeddedRelationshipType",
    "EmbeddedActionType",
    "EmbeddedTicketType",
    "DeleteResult",
    "BulkResult",
    # User type
    "UserType",
    # Pagination
    "Connection",
    "PageInfo",
    "Edge",
    # TLO types
    "ActorType",
    "BackdoorType",
    "CampaignType",
    "CertificateType",
    "DomainType",
    "EmailType",
    "EventType",
    "ExploitType",
    "IndicatorType",
    "IPType",
    "PCAPType",
    "RawDataType",
    "SampleType",
    "ScreenshotType",
    "SignatureType",
    "TargetType",
]
