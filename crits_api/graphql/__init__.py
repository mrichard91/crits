"""GraphQL schema for CRITs API."""

from crits_api.graphql.context import get_context
from crits_api.graphql.schema import schema

__all__ = ["schema", "get_context"]
