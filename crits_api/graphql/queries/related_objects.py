"""Related objects query with BFS traversal of embedded relationships."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.config import settings
from crits_api.graphql.queries.relationships import TLO_TYPE_CONFIG, get_model_class

logger = logging.getLogger(__name__)


@strawberry.type
class RelatedObject:
    """An object found via relationship traversal."""

    id: str
    tlo_type: str
    display_value: str
    relationship: str
    depth: int


@strawberry.type
class RelatedObjectQueries:
    """Queries for traversing TLO relationship graphs."""

    @strawberry.field(description="Get related objects via BFS relationship traversal")
    @require_authenticated
    def related_objects(
        self,
        info: Info,
        id: str,
        tlo_type: str,
        depth: int = 1,
        total_limit: int = 50,
    ) -> list[RelatedObject]:
        """
        Traverse embedded relationships using BFS to find related objects.

        Args:
            id: ObjectId of the starting TLO
            tlo_type: Type of the starting TLO (e.g., "Indicator")
            depth: Maximum traversal depth (default 1, capped by settings)
            total_limit: Maximum total results (default 50, max 200)

        Returns:
            List of RelatedObject with relationship label and depth
        """
        ctx: GraphQLContext = info.context

        if tlo_type not in TLO_TYPE_CONFIG:
            return []

        # Cap depth and limit
        max_depth = min(depth, settings.query_depth_limit)
        total_limit = min(total_limit, 200)

        results: list[RelatedObject] = []
        seen: set[tuple[str, str]] = {(tlo_type, id)}  # (type, id) pairs already visited

        # BFS queue: (obj_type, obj_id, current_depth)
        queue: list[tuple[str, str, int]] = [(tlo_type, id, 0)]

        while queue and len(results) < total_limit:
            current_type, current_id, current_depth = queue.pop(0)

            if current_depth >= max_depth:
                continue

            # Get the object and its embedded relationships
            try:
                obj = _get_object(current_type, current_id)
                if obj is None:
                    continue

                # Check source access
                if not ctx.is_superuser and not _check_source_access(ctx, obj):
                    continue

                relationships = getattr(obj, "relationships", []) or []

                for rel in relationships:
                    rel_type = getattr(rel, "rel_type", "Related To") or "Related To"
                    rel_obj_type = getattr(rel, "type", "") or ""
                    rel_obj_id = str(getattr(rel, "value", ""))

                    if not rel_obj_type or not rel_obj_id:
                        continue

                    key = (rel_obj_type, rel_obj_id)
                    if key in seen:
                        continue
                    seen.add(key)

                    # Resolve the related object
                    related = _resolve_related(ctx, rel_obj_type, rel_obj_id)
                    if related is None:
                        continue

                    results.append(
                        RelatedObject(
                            id=rel_obj_id,
                            tlo_type=rel_obj_type,
                            display_value=related,
                            relationship=rel_type,
                            depth=current_depth + 1,
                        )
                    )

                    if len(results) >= total_limit:
                        break

                    # Enqueue for further traversal
                    if current_depth + 1 < max_depth:
                        queue.append((rel_obj_type, rel_obj_id, current_depth + 1))

            except Exception as e:
                logger.error(
                    "Error traversing relationships for %s/%s: %s",
                    current_type,
                    current_id,
                    e,
                )

        return results


def _get_object(tlo_type: str, obj_id: str) -> object | None:
    """Get a TLO object by type and ID."""
    try:
        from crits.core.class_mapper import class_from_id

        return class_from_id(tlo_type, obj_id)
    except Exception:
        return None


def _check_source_access(ctx: GraphQLContext, obj: object) -> bool:
    """Check if user can access this object based on sources."""
    try:
        if ctx.user and hasattr(ctx.user, "check_source_tlp"):
            return ctx.user.check_source_tlp(obj)
        return True
    except Exception:
        return False


def _resolve_related(ctx: GraphQLContext, tlo_type: str, obj_id: str) -> str | None:
    """
    Resolve a related object and return its display value.
    Returns None if object doesn't exist or user lacks access.
    """
    if tlo_type not in TLO_TYPE_CONFIG:
        return None

    try:
        model_path, _search_field, display_field = TLO_TYPE_CONFIG[tlo_type]
        model_class = get_model_class(model_path)

        queryset = model_class.objects(id=obj_id)

        # Apply source filtering
        if not ctx.is_superuser:
            source_filter = ctx.get_source_filter()
            if source_filter:
                queryset = queryset.filter(__raw__=source_filter)

        obj = queryset.first()
        if obj is None:
            return None

        display = getattr(obj, display_field, None)
        return str(display) if display else str(obj.id)
    except Exception as e:
        logger.debug("Could not resolve %s/%s: %s", tlo_type, obj_id, e)
        return None
