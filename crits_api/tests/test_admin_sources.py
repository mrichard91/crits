"""Tests for admin source management GraphQL operations."""

from crits_api.auth.context import GraphQLContext
from crits_api.tests.conftest import execute_gql


class TestSourceQueries:
    """Test source listing."""

    def test_list_sources_authenticated(self, admin_context: GraphQLContext) -> None:
        result = execute_gql(admin_context, "{ sources { name active sampleCount } }")
        assert result.errors is None
        assert isinstance(result.data["sources"], list)

    def test_list_sources_unauthenticated(self, anon_context: GraphQLContext) -> None:
        result = execute_gql(anon_context, "{ sources { name active } }")
        assert result.errors is not None
        assert (
            "permission" in str(result.errors[0]).lower() or "auth" in str(result.errors[0]).lower()
        )


class TestSourceMutations:
    """Test source CRUD mutations."""

    def test_create_source(self, admin_context: GraphQLContext) -> None:
        result = execute_gql(
            admin_context,
            """
            mutation { createSource(name: "TestApiSource1") { success message id } }
            """,
        )
        assert result.errors is None
        assert result.data["createSource"]["success"] is True
        assert "created" in result.data["createSource"]["message"].lower()

    def test_create_duplicate_source(self, admin_context: GraphQLContext) -> None:
        # Create first
        execute_gql(
            admin_context,
            'mutation { createSource(name: "TestApiSourceDup") { success } }',
        )
        # Try duplicate
        result = execute_gql(
            admin_context,
            'mutation { createSource(name: "TestApiSourceDup") { success message } }',
        )
        assert result.errors is None
        assert result.data["createSource"]["success"] is False
        assert "already exists" in result.data["createSource"]["message"]

    def test_toggle_source(self, admin_context: GraphQLContext) -> None:
        # Create a source first
        execute_gql(
            admin_context,
            'mutation { createSource(name: "TestApiSourceToggle") { success } }',
        )

        # Deactivate
        result = execute_gql(
            admin_context,
            """
            mutation { toggleSource(name: "TestApiSourceToggle", active: false) { success message } }
            """,
        )
        assert result.errors is None
        assert result.data["toggleSource"]["success"] is True
        assert "deactivated" in result.data["toggleSource"]["message"]

        # Verify it's inactive
        list_result = execute_gql(admin_context, "{ sources { name active } }")
        source = next(
            (s for s in list_result.data["sources"] if s["name"] == "TestApiSourceToggle"),
            None,
        )
        assert source is not None
        assert source["active"] is False

        # Reactivate
        result = execute_gql(
            admin_context,
            """
            mutation { toggleSource(name: "TestApiSourceToggle", active: true) { success } }
            """,
        )
        assert result.data["toggleSource"]["success"] is True

    def test_toggle_nonexistent_source(self, admin_context: GraphQLContext) -> None:
        result = execute_gql(
            admin_context,
            """
            mutation { toggleSource(name: "NonExistentSourceXYZ", active: false) { success message } }
            """,
        )
        assert result.errors is None
        assert result.data["toggleSource"]["success"] is False

    def test_create_source_unauthenticated(self, anon_context: GraphQLContext) -> None:
        result = execute_gql(
            anon_context,
            'mutation { createSource(name: "ShouldFail") { success message } }',
        )
        assert result.errors is not None
