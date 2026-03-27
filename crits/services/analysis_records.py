"""Raw MongoDB access helpers for analysis result records."""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Any

from pymongo import DESCENDING, MongoClient
from pymongo.collection import Collection

logger = logging.getLogger(__name__)

ANALYSIS_RECORD_SCHEMA_VERSION = 1


def _env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes"}


def _mongo_client_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "host": os.environ.get("MONGO_HOST", "localhost"),
        "port": int(os.environ.get("MONGO_PORT", 27017)),
    }

    username = os.environ.get("MONGO_USER", "")
    password = os.environ.get("MONGO_PASSWORD", "")
    replicaset = os.environ.get("MONGO_REPLICASET", "")

    if username:
        kwargs["username"] = username
    if password:
        kwargs["password"] = password
    if _env_bool("MONGO_SSL"):
        kwargs["ssl"] = True
    if replicaset:
        kwargs["replicaSet"] = replicaset

    return kwargs


@lru_cache(maxsize=1)
def _get_mongo_client() -> MongoClient[dict[str, Any]]:
    return MongoClient(**_mongo_client_kwargs())


def _get_analysis_results_collection() -> Collection[dict[str, Any]]:
    database_name = os.environ.get("MONGO_DATABASE", "crits")
    return _get_mongo_client()[database_name]["analysis_results"]


def _normalize_config(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    return {}


def _normalize_results(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            normalized.append(dict(item))
        else:
            normalized.append({"result": str(item)})
    return normalized


def _normalize_log_entry(entry: Any) -> dict[str, str]:
    now = str(datetime.now())
    if isinstance(entry, dict):
        return {
            "message": str(entry.get("message", "") or ""),
            "level": str(entry.get("level", "info") or "info"),
            "datetime": str(entry.get("datetime", now) or now),
        }

    return {
        "message": str(getattr(entry, "message", "") or ""),
        "level": str(getattr(entry, "level", "info") or "info"),
        "datetime": str(getattr(entry, "datetime", now) or now),
    }


def _normalize_log_entries(log_entries: Any) -> list[dict[str, str]]:
    if not isinstance(log_entries, list):
        return []
    return [_normalize_log_entry(entry) for entry in log_entries]


def _task_to_document(task: Any) -> dict[str, Any]:
    task_data = task.to_dict()
    analysis_id = str(task_data.get("analysis_id") or task_data.get("id") or task.task_id)
    document: dict[str, Any] = {
        "analysis_id": analysis_id,
        "service_name": str(task_data.get("service_name", "") or ""),
        "template": str(task_data.get("template", "") or ""),
        "distributed": bool(task_data.get("distributed", False)),
        "version": str(task_data.get("version", "") or ""),
        "analyst": str(task_data.get("analyst", "") or ""),
        "source": task_data.get("source"),
        "start_date": str(task_data.get("start_date", "") or ""),
        "finish_date": str(task_data.get("finish_date", "") or ""),
        "status": str(task_data.get("status", "") or ""),
        "config": _normalize_config(task_data.get("config")),
        "log": _normalize_log_entries(task_data.get("log")),
        "results": _normalize_results(task_data.get("results")),
        "object_type": str(task_data.get("object_type", "") or ""),
        "object_id": str(task_data.get("object_id", "") or ""),
        "schema_version": ANALYSIS_RECORD_SCHEMA_VERSION,
    }
    return document


@dataclass(slots=True)
class AnalysisLogRecord:
    message: str = ""
    level: str = ""
    datetime: str = ""

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> AnalysisLogRecord:
        return cls(
            message=str(document.get("message", "") or ""),
            level=str(document.get("level", "") or ""),
            datetime=str(document.get("datetime", "") or ""),
        )


@dataclass(slots=True)
class AnalysisRecord:
    id: str
    analysis_id: str
    service_name: str = ""
    version: str = ""
    object_type: str = ""
    object_id: str = ""
    analyst: str = ""
    status: str = ""
    start_date: str = ""
    finish_date: str = ""
    results: list[dict[str, Any]] = field(default_factory=list)
    log: list[AnalysisLogRecord] = field(default_factory=list)

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> AnalysisRecord:
        return cls(
            id=str(document.get("_id", "")),
            analysis_id=str(document.get("analysis_id", "") or ""),
            service_name=str(document.get("service_name", "") or ""),
            version=str(document.get("version", "") or ""),
            object_type=str(document.get("object_type", "") or ""),
            object_id=str(document.get("object_id", "") or ""),
            analyst=str(document.get("analyst", "") or ""),
            status=str(document.get("status", "") or ""),
            start_date=str(document.get("start_date", "") or ""),
            finish_date=str(document.get("finish_date", "") or ""),
            results=_normalize_results(document.get("results")),
            log=[
                AnalysisLogRecord.from_document(entry)
                for entry in document.get("log", [])
                if isinstance(entry, dict)
            ],
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

    analysis_id = str(uuid.uuid4())
    document: dict[str, Any] = {
        "analysis_id": analysis_id,
        "service_name": service_name,
        "version": version,
        "object_type": obj_type,
        "object_id": str(obj_id),
        "analyst": username,
        "status": "started",
        "start_date": str(datetime.now()),
        "results": [],
        "log": [],
        "schema_version": ANALYSIS_RECORD_SCHEMA_VERSION,
    }

    normalized_config = _normalize_config(config)
    if normalized_config:
        document["config"] = normalized_config

    _get_analysis_results_collection().insert_one(document)
    return analysis_id


def create_analysis_record_from_task(task: Any) -> str:
    """Create or replace a task-backed analysis result document."""

    document = _task_to_document(task)
    analysis_id = str(document["analysis_id"])
    _get_analysis_results_collection().replace_one(
        {"analysis_id": analysis_id},
        document,
        upsert=True,
    )
    return analysis_id


def get_analysis_record(analysis_id: str) -> AnalysisRecord | None:
    """Fetch a single analysis result by analysis_id."""

    document = _get_analysis_results_collection().find_one({"analysis_id": analysis_id})
    if not document:
        return None
    return AnalysisRecord.from_document(document)


def find_analysis_records(
    query: dict[str, Any] | None = None,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[AnalysisRecord]:
    """Fetch analysis results matching a MongoDB query."""

    cursor = (
        _get_analysis_results_collection()
        .find(query or {})
        .sort("start_date", DESCENDING)
        .skip(offset)
        .limit(limit)
    )
    return [AnalysisRecord.from_document(document) for document in cursor]


def finish_analysis_record(analysis_id: str, status: str = "completed") -> None:
    """Update only the status and finish time of an existing analysis record."""

    update_result = _get_analysis_results_collection().update_one(
        {"analysis_id": analysis_id},
        {
            "$set": {
                "status": status,
                "finish_date": str(datetime.now()),
                "schema_version": ANALYSIS_RECORD_SCHEMA_VERSION,
            }
        },
    )

    if update_result.matched_count == 0:
        logger.warning("Analysis record %s not found for finish update", analysis_id)


def update_analysis_record(
    analysis_id: str,
    results: list[dict[str, Any]],
    log_entries: list[dict[str, str]],
    status: str = "completed",
) -> None:
    """Update an existing analysis result document."""

    update_result = _get_analysis_results_collection().update_one(
        {"analysis_id": analysis_id},
        {
            "$set": {
                "results": list(results),
                "log": _normalize_log_entries(log_entries),
                "status": status,
                "finish_date": str(datetime.now()),
                "schema_version": ANALYSIS_RECORD_SCHEMA_VERSION,
            }
        },
    )

    if update_result.matched_count == 0:
        logger.warning("Analysis record %s not found for update", analysis_id)


def update_analysis_record_from_task(task: Any) -> None:
    """Replace a task-backed analysis result document."""

    document = _task_to_document(task)
    _get_analysis_results_collection().replace_one(
        {"analysis_id": str(document["analysis_id"])},
        document,
        upsert=False,
    )


def mark_analysis_error(analysis_id: str, error_message: str) -> None:
    """Mark an analysis result as errored and append an error log."""

    update_result = _get_analysis_results_collection().update_one(
        {"analysis_id": analysis_id},
        {
            "$set": {
                "status": "error",
                "finish_date": str(datetime.now()),
                "schema_version": ANALYSIS_RECORD_SCHEMA_VERSION,
            },
            "$push": {
                "log": {
                    "message": error_message,
                    "level": "error",
                    "datetime": str(datetime.now()),
                }
            },
        },
    )

    if update_result.matched_count == 0:
        logger.warning("Analysis record %s not found for error marking", analysis_id)
