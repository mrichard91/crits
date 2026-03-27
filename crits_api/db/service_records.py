"""Compatibility wrapper for raw service-record helpers."""

from crits.services.service_records import (
    SERVICE_RECORD_SCHEMA_VERSION,
    ServiceRecord,
    find_service_records,
    get_service_record,
    list_service_names,
    update_service_record,
)

__all__ = [
    "SERVICE_RECORD_SCHEMA_VERSION",
    "ServiceRecord",
    "find_service_records",
    "get_service_record",
    "list_service_names",
    "update_service_record",
]
