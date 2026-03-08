"""
Shared sorting utility for TLO list queries.
"""

from typing import Any


def apply_sorting(
    queryset: Any,
    sort_by: str | None,
    sort_dir: str | None,
    allowed_fields: dict[str, str],
) -> Any:
    """Apply sorting to a MongoEngine queryset.

    Args:
        queryset: MongoEngine queryset
        sort_by: camelCase field name from GraphQL (e.g. "indType")
        sort_dir: "asc" or "desc"
        allowed_fields: maps camelCase GraphQL names to MongoEngine field names
            e.g. {"indType": "ind_type", "modified": "modified"}

    Returns:
        Queryset with ordering applied.  Falls back to ``-modified``.
    """
    if sort_by and sort_by in allowed_fields:
        field = allowed_fields[sort_by]
        if sort_dir == "desc":
            field = f"-{field}"
        return queryset.order_by(field)
    return queryset.order_by("-modified")
