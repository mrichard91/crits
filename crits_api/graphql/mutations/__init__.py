"""GraphQL mutation resolvers."""

from crits_api.graphql.mutations.actors import ActorMutations
from crits_api.graphql.mutations.auth import AuthMutations
from crits_api.graphql.mutations.backdoors import BackdoorMutations
from crits_api.graphql.mutations.bulk import BulkMutations
from crits_api.graphql.mutations.campaigns import CampaignMutations
from crits_api.graphql.mutations.certificates import CertificateMutations
from crits_api.graphql.mutations.comments import CommentMutations
from crits_api.graphql.mutations.domains import DomainMutations
from crits_api.graphql.mutations.emails import EmailMutations
from crits_api.graphql.mutations.events import EventMutations
from crits_api.graphql.mutations.exploits import ExploitMutations
from crits_api.graphql.mutations.indicators import IndicatorMutations
from crits_api.graphql.mutations.ips import IPMutations
from crits_api.graphql.mutations.pcaps import PCAPMutations
from crits_api.graphql.mutations.raw_data import RawDataMutations
from crits_api.graphql.mutations.relationships import RelationshipMutations
from crits_api.graphql.mutations.samples import SampleMutations
from crits_api.graphql.mutations.screenshots import ScreenshotMutations
from crits_api.graphql.mutations.services import ServiceMutations
from crits_api.graphql.mutations.signatures import SignatureMutations
from crits_api.graphql.mutations.targets import TargetMutations

__all__ = [
    "AuthMutations",
    "ActorMutations",
    "BackdoorMutations",
    "BulkMutations",
    "CampaignMutations",
    "CertificateMutations",
    "CommentMutations",
    "DomainMutations",
    "EmailMutations",
    "EventMutations",
    "ExploitMutations",
    "IndicatorMutations",
    "IPMutations",
    "PCAPMutations",
    "RawDataMutations",
    "RelationshipMutations",
    "SampleMutations",
    "ScreenshotMutations",
    "ServiceMutations",
    "SignatureMutations",
    "TargetMutations",
]
