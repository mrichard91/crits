"""Analysis result DB operations backed by raw Mongo documents."""

from typing import Any

from crits_api.db.analysis_records import (
    create_analysis_record as _create_analysis_record,
)
from crits_api.db.analysis_records import (
    mark_analysis_error as _mark_analysis_error,
)
from crits_api.db.analysis_records import (
    update_analysis_record as _update_analysis_record,
)


def create_analysis_record(
    service_name: str,
    version: str,
    obj_type: str,
    obj_id: str,
    username: str,
    config: dict[str, Any] | None = None,
) -> str:
    """Create a new analysis result document."""

    return _create_analysis_record(
        service_name=service_name,
        version=version,
        obj_type=obj_type,
        obj_id=obj_id,
        username=username,
        config=config,
    )


def update_analysis_record(
    analysis_id: str,
    results: list[dict[str, Any]],
    log_entries: list[dict[str, str]],
    status: str = "completed",
) -> None:
    """Update an analysis result document."""

    _update_analysis_record(
        analysis_id=analysis_id,
        results=results,
        log_entries=log_entries,
        status=status,
    )


def mark_analysis_error(analysis_id: str, error_message: str) -> None:
    """Mark an analysis result as errored with an error log entry."""

    _mark_analysis_error(
        analysis_id=analysis_id,
        error_message=error_message,
    )
