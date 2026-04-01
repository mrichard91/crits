"""Tests for admin user GraphQL queries."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from django.contrib.auth.hashers import check_password

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


class TestAdminUserMutations:
    """Test admin user mutation behavior."""

    @pytest.fixture()
    def mutation_context(self, admin_context: GraphQLContext) -> GraphQLContext:
        request = MagicMock()
        request.cookies = {}
        request.headers = {}
        request.client = MagicMock(host="127.0.0.1")
        return GraphQLContext(
            request=request,
            response=MagicMock(),
            user=admin_context.user,
        )

    def test_create_user(self, mutation_context: GraphQLContext) -> None:
        result = execute_gql(
            mutation_context,
            """
            mutation {
                createUser(
                    username: "TestApiUserCreate"
                    password: "Abcd1234!"
                    email: "Person@EXAMPLE.COM"
                    firstName: "Test"
                    lastName: "Create"
                ) {
                    success message id
                }
            }
            """,
        )
        assert result.errors is None
        assert result.data["createUser"]["success"] is True

        list_result = execute_gql(
            mutation_context,
            "{ users { username email firstName lastName } }",
        )
        user = next(
            item for item in list_result.data["users"] if item["username"] == "TestApiUserCreate"
        )
        assert user["email"] == "Person@example.com"
        assert user["firstName"] == "Test"
        assert user["lastName"] == "Create"

    def test_create_duplicate_user(self, mutation_context: GraphQLContext) -> None:
        execute_gql(
            mutation_context,
            """
            mutation {
                createUser(username: "TestApiUserDup", password: "Abcd1234!") {
                    success
                }
            }
            """,
        )
        result = execute_gql(
            mutation_context,
            """
            mutation {
                createUser(username: "TestApiUserDup", password: "Abcd1234!") {
                    success message
                }
            }
            """,
        )
        assert result.errors is None
        assert result.data["createUser"]["success"] is False
        assert "already exists" in result.data["createUser"]["message"]

    def test_update_user(self, mutation_context: GraphQLContext) -> None:
        create_result = execute_gql(
            mutation_context,
            """
            mutation {
                createUser(username: "TestApiUserUpdate", password: "Abcd1234!") {
                    success id
                }
            }
            """,
        )
        user_id = create_result.data["createUser"]["id"]

        result = execute_gql(
            mutation_context,
            f"""
            mutation {{
                updateUser(
                    id: "{user_id}"
                    email: "updated@example.com"
                    firstName: "Updated"
                    lastName: "User"
                    organization: "Test Org"
                ) {{
                    success message
                }}
            }}
            """,
        )
        assert result.errors is None
        assert result.data["updateUser"]["success"] is True

        query_result = execute_gql(
            mutation_context,
            f'{{ user(id: "{user_id}") {{ email firstName lastName organization }} }}',
        )
        assert query_result.data["user"]["email"] == "updated@example.com"
        assert query_result.data["user"]["firstName"] == "Updated"
        assert query_result.data["user"]["lastName"] == "User"
        assert query_result.data["user"]["organization"] == "Test Org"

    def test_toggle_user_active(self, mutation_context: GraphQLContext) -> None:
        create_result = execute_gql(
            mutation_context,
            """
            mutation {
                createUser(username: "TestApiUserToggle", password: "Abcd1234!") {
                    success id
                }
            }
            """,
        )
        user_id = create_result.data["createUser"]["id"]

        result = execute_gql(
            mutation_context,
            f'mutation {{ toggleUserActive(id: "{user_id}", active: false) {{ success message }} }}',
        )
        assert result.errors is None
        assert result.data["toggleUserActive"]["success"] is True

        query_result = execute_gql(
            mutation_context,
            f'{{ user(id: "{user_id}") {{ isActive }} }}',
        )
        assert query_result.data["user"]["isActive"] is False

    def test_set_user_roles(self, mutation_context: GraphQLContext) -> None:
        execute_gql(
            mutation_context,
            """
            mutation {
                createRole(name: "TestApiUserRole", description: "role for user tests") {
                    success
                }
            }
            """,
        )
        create_result = execute_gql(
            mutation_context,
            """
            mutation {
                createUser(username: "TestApiUserRoles", password: "Abcd1234!") {
                    success id
                }
            }
            """,
        )
        user_id = create_result.data["createUser"]["id"]

        result = execute_gql(
            mutation_context,
            f"""
            mutation {{
                setUserRoles(id: "{user_id}", roles: ["TestApiUserRole"]) {{
                    success message
                }}
            }}
            """,
        )
        assert result.errors is None
        assert result.data["setUserRoles"]["success"] is True

        query_result = execute_gql(
            mutation_context,
            f'{{ user(id: "{user_id}") {{ roles }} }}',
        )
        assert query_result.data["user"]["roles"] == ["TestApiUserRole"]

    def test_reset_user_password(self, mutation_context: GraphQLContext) -> None:
        from crits.core.user import CRITsUser

        create_result = execute_gql(
            mutation_context,
            """
            mutation {
                createUser(username: "TestApiUserPassword", password: "Abcd1234!") {
                    success id
                }
            }
            """,
        )
        user_id = create_result.data["createUser"]["id"]

        result = execute_gql(
            mutation_context,
            f"""
            mutation {{
                resetUserPassword(id: "{user_id}", newPassword: "Zyxw9876!") {{
                    success message
                }}
            }}
            """,
        )
        assert result.errors is None
        assert result.data["resetUserPassword"]["success"] is True

        user = CRITsUser.objects(username="TestApiUserPassword").first()
        assert user is not None
        assert check_password("Zyxw9876!", user.password)

    def test_reset_user_password_rejects_weak_password(
        self, mutation_context: GraphQLContext
    ) -> None:
        create_result = execute_gql(
            mutation_context,
            """
            mutation {
                createUser(username: "TestApiUserWeakPassword", password: "Abcd1234!") {
                    success id
                }
            }
            """,
        )
        user_id = create_result.data["createUser"]["id"]

        result = execute_gql(
            mutation_context,
            f"""
            mutation {{
                resetUserPassword(id: "{user_id}", newPassword: "weak") {{
                    success message
                }}
            }}
            """,
        )
        assert result.errors is None
        assert result.data["resetUserPassword"]["success"] is False
        assert "complexity" in result.data["resetUserPassword"]["message"].lower()
