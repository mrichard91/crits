"""Database utilities for CRITs GraphQL API."""

from crits_api.db.connection import connect_mongodb, is_connected

__all__ = ["connect_mongodb", "is_connected"]
