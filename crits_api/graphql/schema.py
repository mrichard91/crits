"""
Main GraphQL schema for CRITs API.

Combines all query and mutation types into a single schema.
"""

import strawberry
from strawberry.extensions import QueryDepthLimiter
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.config import settings
from crits_api.graphql.extensions import QueryComplexityLimiter
from crits_api.graphql.mutations import (
    ActorMutations,
    AuthMutations,
    BackdoorMutations,
    BulkMutations,
    CampaignMutations,
    CertificateMutations,
    CommentMutations,
    DomainMutations,
    EmailMutations,
    EventMutations,
    ExploitMutations,
    IndicatorMutations,
    IPMutations,
    PCAPMutations,
    RawDataMutations,
    RelationshipMutations,
    SampleMutations,
    ScreenshotMutations,
    ServiceMutations,
    SignatureMutations,
    TargetMutations,
)
from crits_api.graphql.queries.actors import ActorQueries
from crits_api.graphql.queries.backdoors import BackdoorQueries
from crits_api.graphql.queries.campaigns import CampaignQueries
from crits_api.graphql.queries.certificates import CertificateQueries
from crits_api.graphql.queries.dashboard import DashboardQueries
from crits_api.graphql.queries.domains import DomainQueries
from crits_api.graphql.queries.emails import EmailQueries
from crits_api.graphql.queries.events import EventQueries
from crits_api.graphql.queries.exploits import ExploitQueries

# Import all query classes
from crits_api.graphql.queries.indicators import IndicatorQueries
from crits_api.graphql.queries.ips import IPQueries
from crits_api.graphql.queries.pcaps import PCAPQueries
from crits_api.graphql.queries.raw_data import RawDataQueries
from crits_api.graphql.queries.related_objects import RelatedObjectQueries
from crits_api.graphql.queries.relationships import RelationshipQueries
from crits_api.graphql.queries.samples import SampleQueries
from crits_api.graphql.queries.screenshots import ScreenshotQueries
from crits_api.graphql.queries.search import SearchQueries
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
    DashboardQueries,
    DomainQueries,
    EmailQueries,
    EventQueries,
    ExploitQueries,
    IPQueries,
    PCAPQueries,
    RawDataQueries,
    RelatedObjectQueries,
    RelationshipQueries,
    SampleQueries,
    ScreenshotQueries,
    SearchQueries,
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

    @strawberry.field(description="Get source names the current user can write to")
    @require_authenticated
    def source_names(self, info: Info) -> list[str]:
        """Get list of source names the user has write access to."""
        ctx: GraphQLContext = info.context
        if ctx.is_superuser:
            return sorted(s.name for s in ctx.sources)
        return sorted(s.name for s in ctx.sources if s.write)

    @strawberry.field(description="List available TLO types")
    def tlo_types(self) -> list[TLOType]:
        """Get list of all Top-Level Object types."""
        return list(TLOType)


@strawberry.type
class Mutation(
    AuthMutations,
    IndicatorMutations,
    ActorMutations,
    BackdoorMutations,
    BulkMutations,
    CampaignMutations,
    CertificateMutations,
    CommentMutations,
    DomainMutations,
    EmailMutations,
    EventMutations,
    ExploitMutations,
    IPMutations,
    PCAPMutations,
    RawDataMutations,
    RelationshipMutations,
    SampleMutations,
    ScreenshotMutations,
    ServiceMutations,
    SignatureMutations,
    TargetMutations,
):
    """Root mutation type for CRITs GraphQL API."""

    @strawberry.mutation(description="Test mutation - returns a greeting")
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
    extensions=[
        QueryDepthLimiter(max_depth=settings.query_depth_limit),
        QueryComplexityLimiter,
    ],
)
