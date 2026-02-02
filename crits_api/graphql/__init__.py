"""GraphQL schema for CRITs API."""

from crits_api.graphql.schema import schema
from crits_api.graphql.context import get_context

__all__ = ["schema", "get_context"]
