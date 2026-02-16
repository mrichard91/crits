"""
GraphQL request context for CRITs API.

Contains user information, permissions, and source access for each request.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from fastapi import Request
from starlette.responses import Response
from strawberry.fastapi import BaseContext

if TYPE_CHECKING:
    from crits.core.user import CRITsUser

logger = logging.getLogger(__name__)


@dataclass
class SourceAccess:
    """User's access to a specific source."""

    name: str
    read: bool = False
    write: bool = False
    tlp_red: bool = False
    tlp_amber: bool = False
    tlp_green: bool = False


@dataclass
class GraphQLContext(BaseContext):
    """
    Context object passed to all GraphQL resolvers.

    Contains the authenticated user, their merged ACL permissions,
    and their source access list for data filtering.
    """

    request: Request
    response: Response | None = None
    user: Optional["CRITsUser"] = None
    acl: dict[str, Any] = field(default_factory=dict)
    sources: list[SourceAccess] = field(default_factory=list)
    _sources_hash: str | None = field(default=None, repr=False)

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.user is not None and self.user.is_active

    @property
    def is_superuser(self) -> bool:
        """Check if user is a superuser (bypasses all permission checks)."""
        return self.user is not None and getattr(self.user, "is_superuser", False)

    @property
    def sources_hash(self) -> str:
        """
        Generate a hash of user's source access for cache key generation.

        This ensures cached data is not leaked across users with different
        source access permissions.
        """
        if self._sources_hash is None:
            if not self.sources:
                self._sources_hash = "no_sources"
            else:
                # Create deterministic hash of source access
                source_str = "|".join(
                    f"{s.name}:{s.read}:{s.write}:{s.tlp_red}:{s.tlp_amber}:{s.tlp_green}"
                    for s in sorted(self.sources, key=lambda x: x.name)
                )
                self._sources_hash = hashlib.md5(source_str.encode()).hexdigest()[:12]
        return self._sources_hash

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            permission: Permission string like "Sample.read" or "api_interface"

        Returns:
            True if user has the permission
        """
        if self.is_superuser:
            return True

        if not self.user:
            return False

        # Use the user's has_access_to method which handles ACL merging
        return self.user.has_access_to(permission)

    def get_source_filter(self) -> dict:
        """
        Get MongoDB filter query for source/TLP-based access control.

        Returns a query dict that filters documents to only those
        the user has access to based on their source permissions.
        """
        if self.is_superuser:
            return {}

        if not self.user:
            return {"_id": None}  # Match nothing

        # Use the user's filter method
        return self.user.filter_dict_source_tlp({})

    def can_access_source(self, source_name: str, write: bool = False) -> bool:
        """
        Check if user can access a specific source.

        Args:
            source_name: Name of the source
            write: If True, check write access; otherwise check read access

        Returns:
            True if user has access
        """
        if self.is_superuser:
            return True

        for source in self.sources:
            if source.name == source_name:
                return source.write if write else source.read

        return False

    def get_readable_sources(self, tlp: str | None = None) -> list[str]:
        """
        Get list of source names the user can read.

        Args:
            tlp: Optional TLP level to filter by (red, amber, green, white)

        Returns:
            List of source names
        """
        if self.is_superuser:
            # Superuser can read all sources
            return [s.name for s in self.sources]

        result = []
        for source in self.sources:
            if not source.read:
                continue

            if (
                tlp is None
                or tlp == "white"
                or tlp == "green"
                and source.tlp_green
                or tlp == "amber"
                and source.tlp_amber
                or tlp == "red"
                and source.tlp_red
            ):
                result.append(source.name)

        return result
