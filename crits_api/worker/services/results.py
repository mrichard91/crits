"""Analysis result DB operations using the legacy AnalysisResult MongoEngine model.

Writes to the same `analysis_results` collection so both Django UI and React UI
can read the same data.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def create_analysis_record(
    service_name: str,
    version: str,
    obj_type: str,
    obj_id: str,
    username: str,
    config: dict[str, Any] | None = None,
) -> str:
    """Create a new AnalysisResult document with status='started'.

    Returns the analysis_id (UUID string).
    """
    from crits.services.analysis_result import AnalysisConfig, AnalysisResult

    analysis_id = str(uuid.uuid4())

    ar = AnalysisResult()
    ar.analysis_id = analysis_id
    ar.service_name = service_name
    ar.version = version
    ar.object_type = obj_type
    ar.object_id = str(obj_id)
    ar.analyst = username
    ar.status = "started"
    ar.start_date = str(datetime.now())
    ar.results = []
    ar.log = []

    if config:
        ar.config = AnalysisConfig(**config)

    try:
        ar.save()
        logger.debug("Created analysis record %s for %s/%s", analysis_id, obj_type, obj_id)
    except Exception as e:
        logger.error("Failed to create analysis record: %s", e)
        raise

    return analysis_id


def update_analysis_record(
    analysis_id: str,
    results: list[dict[str, Any]],
    log_entries: list[dict[str, str]],
    status: str = "completed",
) -> None:
    """Update an AnalysisResult with final results, logs, and status."""
    from crits.services.analysis_result import AnalysisResult, EmbeddedAnalysisResultLog

    ar = AnalysisResult.objects(analysis_id=analysis_id).first()
    if not ar:
        logger.warning("Analysis record %s not found for update", analysis_id)
        return

    log_docs = []
    for entry in log_entries:
        log_doc = EmbeddedAnalysisResultLog()
        log_doc.message = entry.get("message", "")
        log_doc.level = entry.get("level", "info")
        log_doc.datetime = entry.get("datetime", str(datetime.now()))
        log_docs.append(log_doc)

    try:
        AnalysisResult.objects(id=ar.id).update_one(
            set__results=results,
            set__log=log_docs,
            set__status=status,
            set__finish_date=str(datetime.now()),
        )
        logger.debug("Updated analysis record %s -> %s", analysis_id, status)
    except Exception as e:
        logger.error("Failed to update analysis record %s: %s", analysis_id, e)
        raise


def mark_analysis_error(analysis_id: str, error_message: str) -> None:
    """Mark an analysis record as errored with an error log entry."""
    from crits.services.analysis_result import AnalysisResult, EmbeddedAnalysisResultLog

    ar = AnalysisResult.objects(analysis_id=analysis_id).first()
    if not ar:
        logger.warning("Analysis record %s not found for error marking", analysis_id)
        return

    log_doc = EmbeddedAnalysisResultLog()
    log_doc.message = error_message
    log_doc.level = "error"
    log_doc.datetime = str(datetime.now())

    try:
        AnalysisResult.objects(id=ar.id).update_one(
            set__status="error",
            set__finish_date=str(datetime.now()),
            push__log=log_doc,
        )
        logger.debug("Marked analysis record %s as error", analysis_id)
    except Exception as e:
        logger.error("Failed to mark analysis record %s as error: %s", analysis_id, e)
