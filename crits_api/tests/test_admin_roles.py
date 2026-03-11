"""Tests for admin role management GraphQL operations."""

import pytest

from crits_api.auth.context import GraphQLContext
from crits_api.tests.conftest import execute_gql

ROLE_FIELDS = """
    id name active description
    sources { name read write tlpRed tlpAmber tlpGreen }
    apiInterface scriptInterface webInterface
    controlPanelRead controlPanelUsersRead controlPanelUsersAdd
    controlPanelUsersEdit controlPanelRolesRead controlPanelRolesEdit
    controlPanelServicesRead controlPanelServicesEdit controlPanelAuditLogRead
"""


class TestRoleQueries:
    """Test role listing and detail."""

    def test_list_roles(self, admin_context: GraphQLContext) -> None:
        result = execute_gql(admin_context, "{ roles { id name active } }")
        assert result.errors is None
        assert isinstance(result.data["roles"], list)

    def test_list_roles_with_permissions(self, admin_context: GraphQLContext) -> None:
        result = execute_gql(
            admin_context,
            f"{{ roles {{ {ROLE_FIELDS} }} }}",
        )
        assert result.errors is None
        for role in result.data["roles"]:
            assert "apiInterface" in role
            assert "controlPanelRead" in role

    def test_list_roles_unauthenticated(self, anon_context: GraphQLContext) -> None:
        result = execute_gql(anon_context, "{ roles { id name } }")
        assert result.errors is not None


class TestRoleMutations:
    """Test role CRUD mutations."""

    def test_create_role(self, admin_context: GraphQLContext) -> None:
        result = execute_gql(
            admin_context,
            """
            mutation {
                createRole(name: "TestApiRole1", description: "Test role for API tests") {
                    success message id
                }
            }
            """,
        )
        assert result.errors is None
        assert result.data["createRole"]["success"] is True
        assert result.data["createRole"]["id"] is not None

    def test_create_duplicate_role(self, admin_context: GraphQLContext) -> None:
        execute_gql(
            admin_context,
            'mutation { createRole(name: "TestApiRoleDup") { success } }',
        )
        result = execute_gql(
            admin_context,
            'mutation { createRole(name: "TestApiRoleDup") { success message } }',
        )
        assert result.data["createRole"]["success"] is False
        assert "already exists" in result.data["createRole"]["message"]

    def test_toggle_role(self, admin_context: GraphQLContext) -> None:
        # Create
        create_result = execute_gql(
            admin_context,
            'mutation { createRole(name: "TestApiRoleToggle") { success id } }',
        )
        role_id = create_result.data["createRole"]["id"]

        # Deactivate
        result = execute_gql(
            admin_context,
            f'mutation {{ toggleRole(id: "{role_id}", active: false) {{ success message }} }}',
        )
        assert result.data["toggleRole"]["success"] is True
        assert "deactivated" in result.data["toggleRole"]["message"]

    def test_update_role(self, admin_context: GraphQLContext) -> None:
        # Create
        create_result = execute_gql(
            admin_context,
            'mutation { createRole(name: "TestApiRoleUpdate") { success id } }',
        )
        role_id = create_result.data["createRole"]["id"]

        # Update
        result = execute_gql(
            admin_context,
            f"""
            mutation {{
                updateRole(id: "{role_id}", name: "TestApiRoleUpdated", description: "Updated description") {{
                    success message
                }}
            }}
            """,
        )
        assert result.errors is None
        assert result.data["updateRole"]["success"] is True


class TestRolePermissions:
    """Test role permission management."""

    def test_set_permission(self, admin_context: GraphQLContext) -> None:
        # Create role
        create_result = execute_gql(
            admin_context,
            'mutation { createRole(name: "TestApiRolePerm") { success id } }',
        )
        role_id = create_result.data["createRole"]["id"]

        # Set a permission
        result = execute_gql(
            admin_context,
            f"""
            mutation {{
                setRolePermission(id: "{role_id}", permission: "api_interface", value: true) {{
                    success message
                }}
            }}
            """,
        )
        assert result.errors is None
        assert result.data["setRolePermission"]["success"] is True

        # Verify the permission is set
        role_result = execute_gql(
            admin_context,
            f'{{ role(id: "{role_id}") {{ apiInterface }} }}',
        )
        assert role_result.data["role"]["apiInterface"] is True

    def test_set_multiple_permissions(self, admin_context: GraphQLContext) -> None:
        create_result = execute_gql(
            admin_context,
            'mutation { createRole(name: "TestApiRoleMultiPerm") { success id } }',
        )
        role_id = create_result.data["createRole"]["id"]

        # Set several permissions
        for perm in ["web_interface", "control_panel_read", "control_panel_users_read"]:
            result = execute_gql(
                admin_context,
                f"""
                mutation {{
                    setRolePermission(id: "{role_id}", permission: "{perm}", value: true) {{
                        success
                    }}
                }}
                """,
            )
            assert result.data["setRolePermission"]["success"] is True

        # Verify all set
        role_result = execute_gql(
            admin_context,
            f'{{ role(id: "{role_id}") {{ webInterface controlPanelRead controlPanelUsersRead }} }}',
        )
        assert role_result.data["role"]["webInterface"] is True
        assert role_result.data["role"]["controlPanelRead"] is True
        assert role_result.data["role"]["controlPanelUsersRead"] is True

    def test_set_invalid_permission(self, admin_context: GraphQLContext) -> None:
        create_result = execute_gql(
            admin_context,
            'mutation { createRole(name: "TestApiRoleBadPerm") { success id } }',
        )
        role_id = create_result.data["createRole"]["id"]

        result = execute_gql(
            admin_context,
            f"""
            mutation {{
                setRolePermission(id: "{role_id}", permission: "totally_fake_permission", value: true) {{
                    success message
                }}
            }}
            """,
        )
        assert result.data["setRolePermission"]["success"] is False
        assert "unknown" in result.data["setRolePermission"]["message"].lower()


class TestRoleSourceACLs:
    """Test role source access control management."""

    @pytest.fixture(autouse=True)
    def _create_test_source(self, admin_context: GraphQLContext) -> None:
        """Ensure a test source exists for ACL tests."""
        execute_gql(
            admin_context,
            'mutation { createSource(name: "TestApiACLSource") { success } }',
        )

    def test_add_source_to_role(self, admin_context: GraphQLContext) -> None:
        create_result = execute_gql(
            admin_context,
            'mutation { createRole(name: "TestApiRoleACL1") { success id } }',
        )
        role_id = create_result.data["createRole"]["id"]

        result = execute_gql(
            admin_context,
            f"""
            mutation {{
                addRoleSource(
                    id: "{role_id}",
                    sourceName: "TestApiACLSource",
                    read: true,
                    write: false,
                    tlpRed: false,
                    tlpAmber: true,
                    tlpGreen: true
                ) {{ success message }}
            }}
            """,
        )
        assert result.errors is None
        assert result.data["addRoleSource"]["success"] is True

        # Verify source is attached
        role_result = execute_gql(
            admin_context,
            f'{{ role(id: "{role_id}") {{ sources {{ name read write tlpAmber tlpGreen }} }} }}',
        )
        sources = role_result.data["role"]["sources"]
        assert len(sources) == 1
        assert sources[0]["name"] == "TestApiACLSource"
        assert sources[0]["read"] is True
        assert sources[0]["write"] is False
        assert sources[0]["tlpAmber"] is True
        assert sources[0]["tlpGreen"] is True

    def test_update_source_flags(self, admin_context: GraphQLContext) -> None:
        """addRoleSource should upsert — update flags on existing source."""
        create_result = execute_gql(
            admin_context,
            'mutation { createRole(name: "TestApiRoleACL2") { success id } }',
        )
        role_id = create_result.data["createRole"]["id"]

        # Add with read only
        execute_gql(
            admin_context,
            f"""
            mutation {{
                addRoleSource(id: "{role_id}", sourceName: "TestApiACLSource",
                    read: true, write: false, tlpRed: false, tlpAmber: false, tlpGreen: false
                ) {{ success }}
            }}
            """,
        )

        # Upsert with write
        execute_gql(
            admin_context,
            f"""
            mutation {{
                addRoleSource(id: "{role_id}", sourceName: "TestApiACLSource",
                    read: true, write: true, tlpRed: true, tlpAmber: false, tlpGreen: false
                ) {{ success }}
            }}
            """,
        )

        # Verify updated flags
        role_result = execute_gql(
            admin_context,
            f'{{ role(id: "{role_id}") {{ sources {{ name read write tlpRed }} }} }}',
        )
        sources = role_result.data["role"]["sources"]
        assert len(sources) == 1
        assert sources[0]["write"] is True
        assert sources[0]["tlpRed"] is True

    def test_remove_source_from_role(self, admin_context: GraphQLContext) -> None:
        create_result = execute_gql(
            admin_context,
            'mutation { createRole(name: "TestApiRoleACL3") { success id } }',
        )
        role_id = create_result.data["createRole"]["id"]

        # Add source
        execute_gql(
            admin_context,
            f"""
            mutation {{
                addRoleSource(id: "{role_id}", sourceName: "TestApiACLSource",
                    read: true, write: false, tlpRed: false, tlpAmber: false, tlpGreen: false
                ) {{ success }}
            }}
            """,
        )

        # Remove it
        result = execute_gql(
            admin_context,
            f"""
            mutation {{
                removeRoleSource(id: "{role_id}", sourceName: "TestApiACLSource") {{
                    success message
                }}
            }}
            """,
        )
        assert result.data["removeRoleSource"]["success"] is True

        # Verify removed
        role_result = execute_gql(
            admin_context,
            f'{{ role(id: "{role_id}") {{ sources {{ name }} }} }}',
        )
        assert len(role_result.data["role"]["sources"]) == 0
