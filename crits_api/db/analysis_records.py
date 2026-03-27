"""Compatibility wrapper for raw analysis-record helpers."""

from crits.services.analysis_records import (
    ANALYSIS_RECORD_SCHEMA_VERSION,
    AnalysisLogRecord,
    AnalysisRecord,
    create_analysis_record,
    create_analysis_record_from_task,
    find_analysis_records,
    finish_analysis_record,
    get_analysis_record,
    mark_analysis_error,
    update_analysis_record,
    update_analysis_record_from_task,
)

__all__ = [
    "ANALYSIS_RECORD_SCHEMA_VERSION",
    "AnalysisLogRecord",
    "AnalysisRecord",
    "create_analysis_record",
    "create_analysis_record_from_task",
    "find_analysis_records",
    "finish_analysis_record",
    "get_analysis_record",
    "mark_analysis_error",
    "update_analysis_record",
    "update_analysis_record_from_task",
]
