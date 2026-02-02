"""
Main GraphQL schema for CRITs API.

Combines all query and mutation types into a single schema.
"""

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.graphql.queries.actors import ActorQueries
from crits_api.graphql.queries.backdoors import BackdoorQueries
from crits_api.graphql.queries.campaigns import CampaignQueries
from crits_api.graphql.queries.certificates import CertificateQueries
from crits_api.graphql.queries.domains import DomainQueries
from crits_api.graphql.queries.emails import EmailQueries
from crits_api.graphql.queries.events import EventQueries
from crits_api.graphql.queries.exploits import ExploitQueries

# Import all query classes
from crits_api.graphql.queries.indicators import IndicatorQueries
from crits_api.graphql.queries.ips import IPQueries
from crits_api.graphql.queries.pcaps import PCAPQueries
from crits_api.graphql.queries.raw_data import RawDataQueries
from crits_api.graphql.queries.samples import SampleQueries
from crits_api.graphql.queries.screenshots import ScreenshotQueries
from crits_api.graphql.queries.signatures import SignatureQueries
from crits_api.graphql.queries.targets import TargetQueries
from crits_api.graphql.types.common import TLOType
from crits_api.graphql.types.user import UserType


@strawberry.type
class Query(
    IndicatorQueries,
    ActorQueries,
    BackdoorQueries,
    CampaignQueries,
    CertificateQueries,
    DomainQueries,
    EmailQueries,
    EventQueries,
    ExploitQueries,
    IPQueries,
    PCAPQueries,
    RawDataQueries,
    SampleQueries,
    ScreenshotQueries,
    SignatureQueries,
    TargetQueries,
):
    """Root query type for CRITs GraphQL API."""

    @strawberry.field(description="Health check - returns API version")
    def health(self) -> str:
        return "CRITs GraphQL API v0.1.0"

    @strawberry.field(description="Get the currently authenticated user")
    @require_authenticated
    def me(self, info: Info) -> UserType:
        """
        Get the current user's information.

        Requires authentication.
        """
        ctx: GraphQLContext = info.context
        return UserType.from_model(ctx.user)

    @strawberry.field(description="Check if user has a specific permission")
    @require_authenticated
    def has_permission(self, info: Info, permission: str) -> bool:
        """
        Check if the current user has a specific permission.

        Args:
            permission: Permission string like "Sample.read" or "api_interface"

        Returns:
            True if user has the permission
        """
        ctx: GraphQLContext = info.context
        return ctx.has_permission(permission)

    @strawberry.field(description="List available TLO types")
    def tlo_types(self) -> list[TLOType]:
        """Get list of all Top-Level Object types."""
        return list(TLOType)


@strawberry.type
class Mutation:
    """Root mutation type for CRITs GraphQL API."""

    @strawberry.mutation(description="Placeholder mutation - API is read-only initially")
    @require_authenticated
    def ping(self, info: Info) -> str:
        """
        Test mutation that returns a greeting.

        Requires authentication.
        """
        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"
        return f"pong from {username}"


# Create the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    # Extensions can be added here for tracing, complexity limiting, etc.
)
