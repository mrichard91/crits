"""
Main GraphQL schema for CRITs API.

Combines all query and mutation types into a single schema.
"""

from typing import Optional

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated, require_permission
from crits_api.graphql.types.user import UserType
from crits_api.graphql.types.common import TLOType
from crits_api.graphql.types.indicator import IndicatorType
from crits_api.graphql.queries.indicators import IndicatorQueries


@strawberry.type
class Query(IndicatorQueries):
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
        return f"pong from {ctx.user.username}"


# Create the schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    # Extensions can be added here for tracing, complexity limiting, etc.
)
