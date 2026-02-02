"""
User GraphQL type for CRITs API.

Exposes user information (excluding sensitive fields like password hashes).
"""

from datetime import datetime
from typing import Any

import strawberry


@strawberry.type
class UserType:
    """
    CRITs user information.

    Excludes sensitive fields like password hash.
    """

    id: str
    username: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    last_login: datetime | None = None
    date_joined: datetime | None = None
    organization: str = ""
    roles: list[str] = strawberry.field(default_factory=list)

    @classmethod
    def from_model(cls, user: Any) -> "UserType":
        """
        Create UserType from CRITsUser MongoEngine model.

        Args:
            user: CRITsUser instance

        Returns:
            UserType instance
        """
        return cls(
            id=str(user.id),
            username=user.username,
            email=getattr(user, "email", "") or "",
            first_name=getattr(user, "first_name", "") or "",
            last_name=getattr(user, "last_name", "") or "",
            is_active=getattr(user, "is_active", True),
            is_staff=getattr(user, "is_staff", False),
            is_superuser=getattr(user, "is_superuser", False),
            last_login=getattr(user, "last_login", None),
            date_joined=getattr(user, "date_joined", None),
            organization=getattr(user, "organization", "") or "",
            roles=list(getattr(user, "roles", []) or []),
        )


@strawberry.type
class RoleType:
    """CRITs role with permissions."""

    id: str
    name: str
    description: str = ""
    active: bool = True

    @classmethod
    def from_model(cls, role: Any) -> "RoleType":
        """Create RoleType from Role MongoEngine model."""
        return cls(
            id=str(role.id),
            name=role.name,
            description=getattr(role, "description", "") or "",
            active=getattr(role, "active", True),
        )
