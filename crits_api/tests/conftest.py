"""
Shared fixtures for CRITs API tests.

Provides a test user, admin context, and schema execution helpers.
Tests run against the real MongoDB instance (inside Docker).
"""

import os
from collections.abc import Generator
from typing import Any

import pytest
from strawberry.types import ExecutionResult

# Ensure Django settings are configured before any model imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crits_api.db.api_settings")

import django  # noqa: E402

django.setup()

from unittest.mock import MagicMock  # noqa: E402

from crits_api.auth.context import GraphQLContext  # noqa: E402
from crits_api.graphql.schema import schema  # noqa: E402

# Test constants
TEST_USER = "test_api_user"
TEST_PASS = "!@#j54kfeimn?>S<D"
TEST_EMAIL = "test_api@example.com"
TEST_SOURCE = "TestApiSource"
TEST_ROLE = "TestApiRole"


def _clean_test_data() -> None:
    """Remove test artifacts from database."""
    from crits.core.role import Role
    from crits.core.source_access import SourceAccess
    from crits.core.user import CRITsUser

    # Clean test user
    CRITsUser.objects(username=TEST_USER).delete()
    # Clean test sources (anything starting with "TestApi")
    SourceAccess.objects(name__startswith="TestApi").delete()
    # Clean test roles
    Role.objects(name__startswith="TestApi").delete()
    # Clean test config items
    try:
        from crits.raw_data.raw_data import RawDataType

        RawDataType.objects(name__startswith="TestApi").delete()
    except Exception:
        pass
    try:
        from crits.signatures.signature import SignatureDependency, SignatureType

        SignatureType.objects(name__startswith="TestApi").delete()
        SignatureDependency.objects(name__startswith="TestApi").delete()
    except Exception:
        pass
    try:
        from crits.core.crits_mongoengine import Action

        Action.objects(name__startswith="TestApi").delete()
    except Exception:
        pass
    # Clean test comments
    try:
        from crits.comments.comment import Comment

        Comment.objects(analyst=TEST_USER).delete()
    except Exception:
        pass
    # Clean test services
    try:
        from crits.services.service_records import delete_service_records

        delete_service_records({"name": {"$regex": "^TestApi"}})
    except Exception:
        pass


@pytest.fixture(autouse=True, scope="session")
def setup_test_db() -> Generator[None]:
    """Create test user and clean up after all tests."""
    from crits.core.user import CRITsUser

    _clean_test_data()

    # Ensure test source exists (needed for creating TLOs in comment tests)
    from crits.core.source_access import SourceAccess

    if not SourceAccess.objects(name="TestApiSource").first():
        sa = SourceAccess(name="TestApiSource", active="on")
        sa.save()

    # Create test user (superuser for admin access)
    user = CRITsUser.create_user(TEST_USER, TEST_PASS, TEST_EMAIL)
    if user:
        user.is_superuser = True
        user.first_name = "Test"
        user.last_name = "User"
        user.organization = "TestApiSource"
        user.save()

    yield

    _clean_test_data()


@pytest.fixture
def test_user() -> Any:
    """Get the test user from the database."""
    from crits.core.user import CRITsUser

    return CRITsUser.objects(username=TEST_USER).first()


@pytest.fixture
def admin_context(test_user: Any) -> GraphQLContext:
    """Create a GraphQLContext with admin (superuser) permissions."""
    request = MagicMock()
    request.cookies = {}
    return GraphQLContext(
        request=request,
        response=MagicMock(),
        user=test_user,
    )


@pytest.fixture
def anon_context() -> GraphQLContext:
    """Create an unauthenticated GraphQLContext."""
    request = MagicMock()
    request.cookies = {}
    return GraphQLContext(
        request=request,
        response=MagicMock(),
        user=None,
    )


def execute_gql(
    context: GraphQLContext, query: str, variables: dict[str, Any] | None = None
) -> ExecutionResult:
    """Execute a GraphQL query/mutation against the schema."""
    result = schema.execute_sync(
        query,
        variable_values=variables,
        context_value=context,
    )
    return result
