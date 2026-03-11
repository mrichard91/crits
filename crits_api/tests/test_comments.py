"""Tests for comment GraphQL operations.

These tests cover the comment add/edit/delete flow,
including the fix for the missing url_key and HttpResponse parsing.
"""

import contextlib
from collections.abc import Generator
from typing import Any

import pytest

from crits_api.auth.context import GraphQLContext
from crits_api.tests.conftest import TEST_USER, execute_gql


@pytest.fixture
def sample_indicator(admin_context: GraphQLContext) -> Generator[Any]:
    """Create a test indicator to attach comments to."""
    from crits.core.crits_mongoengine import create_embedded_source
    from crits.indicators.indicator import Indicator

    ind = Indicator()
    ind.value = "test-comment-indicator.example.com"
    ind.ind_type = "URI - Domain Name"
    source = create_embedded_source(name="TestApiSource", analyst=TEST_USER, needs_tlp=False)
    ind.source = [source]
    ind.save(username=TEST_USER)
    yield ind
    with contextlib.suppress(Exception):
        ind.delete()


class TestCommentQueries:
    """Test comment listing."""

    def test_list_comments_empty(
        self, admin_context: GraphQLContext, sample_indicator: Any
    ) -> None:
        result = execute_gql(
            admin_context,
            """
            query Comments($objType: String!, $objId: String!) {
                comments(objType: $objType, objId: $objId) {
                    id comment analyst created editDate parentDate parentAnalyst
                }
            }
            """,
            variables={"objType": "Indicator", "objId": str(sample_indicator.id)},
        )
        assert result.errors is None
        assert result.data["comments"] == []

    def test_list_comments_unauthenticated(
        self, anon_context: GraphQLContext, sample_indicator: Any
    ) -> None:
        result = execute_gql(
            anon_context,
            """
            query { comments(objType: "Indicator", objId: "fake") { id } }
            """,
        )
        assert result.errors is not None


class TestAddComment:
    """Test adding comments — validates the url_key and HttpResponse fix."""

    def test_add_comment(self, admin_context: GraphQLContext, sample_indicator: Any) -> None:
        obj_id = str(sample_indicator.id)

        result = execute_gql(
            admin_context,
            """
            mutation AddComment($objType: String!, $objId: String!, $comment: String!) {
                addComment(objType: $objType, objId: $objId, comment: $comment) {
                    success message
                }
            }
            """,
            variables={
                "objType": "Indicator",
                "objId": obj_id,
                "comment": "This is a test comment",
            },
        )
        assert result.errors is None
        assert result.data["addComment"]["success"] is True

        # Verify the comment now appears in the list
        list_result = execute_gql(
            admin_context,
            """
            query Comments($objType: String!, $objId: String!) {
                comments(objType: $objType, objId: $objId) {
                    comment analyst
                }
            }
            """,
            variables={"objType": "Indicator", "objId": obj_id},
        )
        assert list_result.errors is None
        comments = list_result.data["comments"]
        assert len(comments) >= 1
        assert any(c["comment"] == "This is a test comment" for c in comments)
        assert any(c["analyst"] == TEST_USER for c in comments)

    def test_add_multiple_comments(
        self, admin_context: GraphQLContext, sample_indicator: Any
    ) -> None:
        obj_id = str(sample_indicator.id)

        for i in range(3):
            result = execute_gql(
                admin_context,
                """
                mutation AddComment($objType: String!, $objId: String!, $comment: String!) {
                    addComment(objType: $objType, objId: $objId, comment: $comment) {
                        success
                    }
                }
                """,
                variables={
                    "objType": "Indicator",
                    "objId": obj_id,
                    "comment": f"Comment number {i}",
                },
            )
            assert result.data["addComment"]["success"] is True

        # All should appear
        list_result = execute_gql(
            admin_context,
            """
            query Comments($objType: String!, $objId: String!) {
                comments(objType: $objType, objId: $objId) { comment }
            }
            """,
            variables={"objType": "Indicator", "objId": obj_id},
        )
        comments = list_result.data["comments"]
        assert len(comments) >= 3

    def test_add_reply(self, admin_context: GraphQLContext, sample_indicator: Any) -> None:
        obj_id = str(sample_indicator.id)

        # Add parent comment
        execute_gql(
            admin_context,
            """
            mutation AddComment($objType: String!, $objId: String!, $comment: String!) {
                addComment(objType: $objType, objId: $objId, comment: $comment) { success }
            }
            """,
            variables={
                "objType": "Indicator",
                "objId": obj_id,
                "comment": "Parent comment for reply test",
            },
        )

        # Get the parent comment's date
        list_result = execute_gql(
            admin_context,
            """
            query Comments($objType: String!, $objId: String!) {
                comments(objType: $objType, objId: $objId) {
                    comment analyst created
                }
            }
            """,
            variables={"objType": "Indicator", "objId": obj_id},
        )
        parent = next(
            c
            for c in list_result.data["comments"]
            if c["comment"] == "Parent comment for reply test"
        )

        # Add reply
        result = execute_gql(
            admin_context,
            """
            mutation AddComment($objType: String!, $objId: String!, $comment: String!, $parentDate: String, $parentAnalyst: String) {
                addComment(objType: $objType, objId: $objId, comment: $comment, parentDate: $parentDate, parentAnalyst: $parentAnalyst) {
                    success message
                }
            }
            """,
            variables={
                "objType": "Indicator",
                "objId": obj_id,
                "comment": "This is a reply",
                "parentDate": parent["created"],
                "parentAnalyst": parent["analyst"],
            },
        )
        assert result.errors is None
        assert result.data["addComment"]["success"] is True

        # Verify reply exists with parent info
        list_result = execute_gql(
            admin_context,
            """
            query Comments($objType: String!, $objId: String!) {
                comments(objType: $objType, objId: $objId) {
                    comment parentDate parentAnalyst
                }
            }
            """,
            variables={"objType": "Indicator", "objId": obj_id},
        )
        reply = next(c for c in list_result.data["comments"] if c["comment"] == "This is a reply")
        assert reply["parentDate"] is not None
        assert reply["parentAnalyst"] == TEST_USER

    def test_add_comment_unauthenticated(
        self, anon_context: GraphQLContext, sample_indicator: Any
    ) -> None:
        result = execute_gql(
            anon_context,
            """
            mutation {
                addComment(objType: "Indicator", objId: "fake", comment: "nope") {
                    success
                }
            }
            """,
        )
        assert result.errors is not None


class TestDeleteComment:
    """Test deleting comments."""

    def test_delete_own_comment(self, admin_context: GraphQLContext, sample_indicator: Any) -> None:
        obj_id = str(sample_indicator.id)

        # Add
        execute_gql(
            admin_context,
            """
            mutation AddComment($objType: String!, $objId: String!, $comment: String!) {
                addComment(objType: $objType, objId: $objId, comment: $comment) { success }
            }
            """,
            variables={
                "objType": "Indicator",
                "objId": obj_id,
                "comment": "Comment to delete",
            },
        )

        # Get date
        list_result = execute_gql(
            admin_context,
            """
            query Comments($objType: String!, $objId: String!) {
                comments(objType: $objType, objId: $objId) { comment created }
            }
            """,
            variables={"objType": "Indicator", "objId": obj_id},
        )
        comment = next(
            c for c in list_result.data["comments"] if c["comment"] == "Comment to delete"
        )

        # Delete
        result = execute_gql(
            admin_context,
            """
            mutation DeleteComment($objId: String!, $commentDate: String!) {
                deleteComment(objId: $objId, commentDate: $commentDate) {
                    success message
                }
            }
            """,
            variables={"objId": obj_id, "commentDate": comment["created"]},
        )
        assert result.errors is None
        assert result.data["deleteComment"]["success"] is True

        # Verify gone
        list_result = execute_gql(
            admin_context,
            """
            query Comments($objType: String!, $objId: String!) {
                comments(objType: $objType, objId: $objId) { comment }
            }
            """,
            variables={"objType": "Indicator", "objId": obj_id},
        )
        assert not any(c["comment"] == "Comment to delete" for c in list_result.data["comments"])
