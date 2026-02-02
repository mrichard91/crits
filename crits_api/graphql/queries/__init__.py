"""GraphQL query definitions for CRITs API."""

from crits_api.graphql.queries.actors import ActorQueries
from crits_api.graphql.queries.backdoors import BackdoorQueries
from crits_api.graphql.queries.campaigns import CampaignQueries
from crits_api.graphql.queries.certificates import CertificateQueries
from crits_api.graphql.queries.domains import DomainQueries
from crits_api.graphql.queries.emails import EmailQueries
from crits_api.graphql.queries.events import EventQueries
from crits_api.graphql.queries.exploits import ExploitQueries
from crits_api.graphql.queries.indicators import IndicatorQueries
from crits_api.graphql.queries.ips import IPQueries
from crits_api.graphql.queries.pcaps import PCAPQueries
from crits_api.graphql.queries.raw_data import RawDataQueries
from crits_api.graphql.queries.samples import SampleQueries
from crits_api.graphql.queries.screenshots import ScreenshotQueries
from crits_api.graphql.queries.signatures import SignatureQueries
from crits_api.graphql.queries.targets import TargetQueries

__all__ = [
    "IndicatorQueries",
    "ActorQueries",
    "BackdoorQueries",
    "CampaignQueries",
    "CertificateQueries",
    "DomainQueries",
    "EmailQueries",
    "EventQueries",
    "ExploitQueries",
    "IPQueries",
    "PCAPQueries",
    "RawDataQueries",
    "SampleQueries",
    "ScreenshotQueries",
    "SignatureQueries",
    "TargetQueries",
]
