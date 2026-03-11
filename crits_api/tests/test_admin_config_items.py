"""Tests for admin config item management GraphQL operations."""

import pytest

from crits_api.auth.context import GraphQLContext
from crits_api.tests.conftest import execute_gql

# Each tab in the UI maps to one of these
CONFIG_TYPES = [
    ("RAW_DATA_TYPE", "rawDataTypes"),
    ("SIGNATURE_TYPE", "signatureTypes"),
    ("SIGNATURE_DEPENDENCY", "signatureDependencies"),
    ("ACTION", "actions"),
]


class TestConfigItemQueries:
    """Test config item listing queries."""

    @pytest.mark.parametrize("config_type,query_name", CONFIG_TYPES)
    def test_list_items(
        self, admin_context: GraphQLContext, config_type: str, query_name: str
    ) -> None:
        result = execute_gql(
            admin_context,
            f"{{ {query_name} {{ name active }} }}",
        )
        assert result.errors is None
        assert isinstance(result.data[query_name], list)

    @pytest.mark.parametrize("config_type,query_name", CONFIG_TYPES)
    def test_list_items_unauthenticated(
        self, anon_context: GraphQLContext, config_type: str, query_name: str
    ) -> None:
        result = execute_gql(
            anon_context,
            f"{{ {query_name} {{ name active }} }}",
        )
        assert result.errors is not None


class TestConfigItemMutations:
    """Test config item CRUD mutations."""

    @pytest.mark.parametrize("config_type,query_name", CONFIG_TYPES)
    def test_create_item(
        self, admin_context: GraphQLContext, config_type: str, query_name: str
    ) -> None:
        name = f"TestApi{config_type}Create"
        result = execute_gql(
            admin_context,
            f"""
            mutation {{
                createConfigItem(configType: {config_type}, name: "{name}") {{
                    success message id
                }}
            }}
            """,
        )
        assert result.errors is None
        assert result.data["createConfigItem"]["success"] is True

        # Verify it appears in the list
        list_result = execute_gql(admin_context, f"{{ {query_name} {{ name active }} }}")
        items = list_result.data[query_name]
        match = [i for i in items if i["name"] == name]
        assert len(match) == 1
        assert match[0]["active"] is True

    @pytest.mark.parametrize("config_type,query_name", CONFIG_TYPES)
    def test_create_duplicate_item(
        self, admin_context: GraphQLContext, config_type: str, query_name: str
    ) -> None:
        name = f"TestApi{config_type}Dup"
        execute_gql(
            admin_context,
            f'mutation {{ createConfigItem(configType: {config_type}, name: "{name}") {{ success }} }}',
        )
        result = execute_gql(
            admin_context,
            f'mutation {{ createConfigItem(configType: {config_type}, name: "{name}") {{ success message }} }}',
        )
        assert result.data["createConfigItem"]["success"] is False
        assert "already exists" in result.data["createConfigItem"]["message"]

    @pytest.mark.parametrize("config_type,query_name", CONFIG_TYPES)
    def test_toggle_item(
        self, admin_context: GraphQLContext, config_type: str, query_name: str
    ) -> None:
        name = f"TestApi{config_type}Toggle"
        execute_gql(
            admin_context,
            f'mutation {{ createConfigItem(configType: {config_type}, name: "{name}") {{ success }} }}',
        )

        # Deactivate
        result = execute_gql(
            admin_context,
            f"""
            mutation {{
                toggleConfigItem(configType: {config_type}, name: "{name}", active: false) {{
                    success message
                }}
            }}
            """,
        )
        assert result.data["toggleConfigItem"]["success"] is True
        assert "deactivated" in result.data["toggleConfigItem"]["message"]

        # Verify inactive
        list_result = execute_gql(admin_context, f"{{ {query_name} {{ name active }} }}")
        match = [i for i in list_result.data[query_name] if i["name"] == name]
        assert match[0]["active"] is False

    @pytest.mark.parametrize("config_type,query_name", CONFIG_TYPES)
    def test_delete_item(
        self, admin_context: GraphQLContext, config_type: str, query_name: str
    ) -> None:
        name = f"TestApi{config_type}Del"
        execute_gql(
            admin_context,
            f'mutation {{ createConfigItem(configType: {config_type}, name: "{name}") {{ success }} }}',
        )

        # Delete
        result = execute_gql(
            admin_context,
            f"""
            mutation {{
                deleteConfigItem(configType: {config_type}, name: "{name}") {{
                    success message deletedId
                }}
            }}
            """,
        )
        assert result.errors is None
        assert result.data["deleteConfigItem"]["success"] is True

        # Verify gone
        list_result = execute_gql(admin_context, f"{{ {query_name} {{ name }} }}")
        match = [i for i in list_result.data[query_name] if i["name"] == name]
        assert len(match) == 0

    def test_delete_nonexistent_item(self, admin_context: GraphQLContext) -> None:
        result = execute_gql(
            admin_context,
            """
            mutation {
                deleteConfigItem(configType: ACTION, name: "TotallyNonexistentXYZ") {
                    success message
                }
            }
            """,
        )
        assert result.data["deleteConfigItem"]["success"] is False

    def test_create_item_unauthenticated(self, anon_context: GraphQLContext) -> None:
        result = execute_gql(
            anon_context,
            """
            mutation { createConfigItem(configType: ACTION, name: "ShouldFail") { success } }
            """,
        )
        assert result.errors is not None
