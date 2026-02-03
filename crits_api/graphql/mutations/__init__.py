"""GraphQL mutation resolvers."""

from crits_api.graphql.mutations.actors import ActorMutations
from crits_api.graphql.mutations.backdoors import BackdoorMutations
from crits_api.graphql.mutations.campaigns import CampaignMutations
from crits_api.graphql.mutations.domains import DomainMutations
from crits_api.graphql.mutations.emails import EmailMutations
from crits_api.graphql.mutations.events import EventMutations
from crits_api.graphql.mutations.exploits import ExploitMutations
from crits_api.graphql.mutations.indicators import IndicatorMutations
from crits_api.graphql.mutations.ips import IPMutations
from crits_api.graphql.mutations.targets import TargetMutations

__all__ = [
    "ActorMutations",
    "BackdoorMutations",
    "CampaignMutations",
    "DomainMutations",
    "EmailMutations",
    "EventMutations",
    "ExploitMutations",
    "IndicatorMutations",
    "IPMutations",
    "TargetMutations",
]
