"""
Pagination types for GraphQL queries.

Implements Relay-style cursor-based pagination.
"""

import base64
from typing import Generic, TypeVar, Optional

import strawberry

T = TypeVar("T")


@strawberry.type
class PageInfo:
    """Information about the current page of results."""

    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None
    total_count: int = 0


@strawberry.type
class Edge(Generic[T]):
    """An edge in a connection, containing the node and cursor."""

    node: T
    cursor: str


def make_edge_type(node_type: type) -> type:
    """
    Factory to create a typed Edge class for a specific node type.

    Usage:
        DomainEdge = make_edge_type(DomainType)
    """

    @strawberry.type
    class TypedEdge:
        node: node_type
        cursor: str

    TypedEdge.__name__ = f"{node_type.__name__}Edge"
    return TypedEdge


@strawberry.type
class Connection(Generic[T]):
    """
    A connection of items with pagination info.

    Follows the Relay Connection specification.
    """

    edges: list[Edge[T]]
    page_info: PageInfo
    total_count: int = 0


def encode_cursor(value: str) -> str:
    """
    Encode a cursor value.

    Args:
        value: Raw cursor value (e.g., ObjectId string)

    Returns:
        Base64-encoded cursor
    """
    return base64.b64encode(f"cursor:{value}".encode()).decode()


def decode_cursor(cursor: str) -> str:
    """
    Decode a cursor value.

    Args:
        cursor: Base64-encoded cursor

    Returns:
        Raw cursor value
    """
    try:
        decoded = base64.b64decode(cursor.encode()).decode()
        if decoded.startswith("cursor:"):
            return decoded[7:]
        return decoded
    except Exception:
        return cursor


def paginate(
    items: list,
    first: int = 20,
    after: Optional[str] = None,
    total_count: Optional[int] = None,
) -> tuple[list, PageInfo]:
    """
    Apply cursor-based pagination to a list of items.

    Args:
        items: List of items to paginate
        first: Number of items to return
        after: Cursor to start after
        total_count: Optional total count (if not provided, uses len(items))

    Returns:
        Tuple of (paginated items, PageInfo)
    """
    total = total_count if total_count is not None else len(items)

    # Find start index from cursor
    start_idx = 0
    if after:
        cursor_value = decode_cursor(after)
        for i, item in enumerate(items):
            item_id = str(getattr(item, "id", item))
            if item_id == cursor_value:
                start_idx = i + 1
                break

    # Slice items
    end_idx = start_idx + first
    paginated = items[start_idx:end_idx]

    # Build PageInfo
    page_info = PageInfo(
        has_next_page=end_idx < len(items),
        has_previous_page=start_idx > 0,
        start_cursor=encode_cursor(str(getattr(paginated[0], "id", paginated[0])))
        if paginated
        else None,
        end_cursor=encode_cursor(str(getattr(paginated[-1], "id", paginated[-1])))
        if paginated
        else None,
        total_count=total,
    )

    return paginated, page_info
