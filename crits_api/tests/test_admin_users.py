"""Tests for admin user GraphQL queries."""

from typing import Any

from crits_api.auth.context import GraphQLContext
from crits_api.tests.conftest import TEST_USER, execute_gql


class TestAdminUserQueries:
    """Test admin user listing and detail queries."""

    def test_list_users(self, admin_context: GraphQLContext) -> None:
        result = execute_gql(
            admin_context,
            "{ users { id username email firstName lastName isActive roles totp } }",
        )
        assert result.errors is None
        assert isinstance(result.data["users"], list)
        assert any(user["username"] == TEST_USER for user in result.data["users"])

    def test_get_user(self, admin_context: GraphQLContext, test_user: Any) -> None:
        result = execute_gql(
            admin_context,
            f'{{ user(id: "{test_user.id}") {{ id username email organization isSuperuser }} }}',
        )
        assert result.errors is None
        assert result.data["user"]["username"] == TEST_USER
        assert result.data["user"]["isSuperuser"] is True

    def test_list_users_unauthenticated(self, anon_context: GraphQLContext) -> None:
        result = execute_gql(anon_context, "{ users { id username } }")
        assert result.errors is not None

    def test_get_user_unknown_id(self, admin_context: GraphQLContext) -> None:
        result = execute_gql(
            admin_context,
            '{ user(id: "000000000000000000000000") { id username } }',
        )
        assert result.errors is None
        assert result.data["user"] is None
