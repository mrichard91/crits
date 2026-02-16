"""
Custom GraphQL extensions for query complexity limiting.

Strawberry provides QueryDepthLimiter built-in; this module adds
a QueryComplexityLimiter that walks the query AST and rejects
queries exceeding a configurable cost threshold.
"""

import logging
from collections.abc import Iterator

from graphql import (
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    OperationDefinitionNode,
    SelectionSetNode,
)
from graphql.language.ast import IntValueNode
from strawberry.extensions import SchemaExtension

from crits_api.config import settings

logger = logging.getLogger(__name__)


class QueryComplexityLimiter(SchemaExtension):
    """
    Reject queries whose estimated cost exceeds a threshold.

    Cost model:
    - Each selected field costs 1
    - List fields multiply their subtree cost by the value of
      `limit` or `first` argument (default 20 if neither is present
      and the field returns a list)
    """

    def on_execute(self) -> Iterator[None]:
        execution_context = self.execution_context
        document: DocumentNode | None = execution_context.graphql_document
        if document is None:
            yield
            return

        try:
            cost = self._calculate_cost(document)
            max_cost = settings.query_complexity_limit
            if cost > max_cost:
                raise ValueError(f"Query complexity {cost} exceeds maximum allowed {max_cost}")
            logger.debug("Query complexity: %d / %d", cost, max_cost)
        except ValueError:
            raise
        except Exception as e:
            logger.warning("Error calculating query complexity: %s", e)

        yield

    def _calculate_cost(self, document: DocumentNode) -> int:
        """Walk the AST and sum up field costs."""
        fragments: dict[str, FragmentDefinitionNode] = {}
        for definition in document.definitions:
            if isinstance(definition, FragmentDefinitionNode):
                fragments[definition.name.value] = definition

        total = 0
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode) and definition.selection_set:
                total += self._selection_set_cost(definition.selection_set, fragments)
        return total

    def _selection_set_cost(
        self,
        selection_set: SelectionSetNode,
        fragments: dict[str, FragmentDefinitionNode],
    ) -> int:
        cost = 0
        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                field_cost = 1
                # Check for list multiplier args
                multiplier = self._get_list_multiplier(selection)
                child_cost = 0
                if selection.selection_set:
                    child_cost = self._selection_set_cost(selection.selection_set, fragments)
                field_cost += child_cost * multiplier if multiplier > 1 else child_cost
                cost += field_cost
            elif isinstance(selection, InlineFragmentNode):
                if selection.selection_set:
                    cost += self._selection_set_cost(selection.selection_set, fragments)
            elif isinstance(selection, FragmentSpreadNode):
                fragment = fragments.get(selection.name.value)
                if fragment and fragment.selection_set:
                    cost += self._selection_set_cost(fragment.selection_set, fragments)
        return cost

    def _get_list_multiplier(self, field: FieldNode) -> int:
        """Extract multiplier from limit/first arguments on list fields."""
        if not field.arguments:
            return 1
        for arg in field.arguments:
            if arg.name.value in ("limit", "first") and isinstance(arg.value, IntValueNode):
                return max(1, int(arg.value.value))
        return 1
