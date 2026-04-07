"""Shared raw Mongo lookup helpers for generic GraphQL TLO queries."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from crits_api.db.tlo_records import (
    build_contains_filter,
    coerce_object_id,
    combine_filters,
    count_tlo_records,
    get_tlo_collection,
    get_tlo_record,
    list_tlo_records,
)


@dataclass(frozen=True)
class TLOLookupConfig:
    """Lookup metadata for a CRITs top-level object type."""

    collection_name: str
    search_field: str
    display_field: str


TLO_LOOKUP_CONFIG: dict[str, TLOLookupConfig] = {
    "Actor": TLOLookupConfig("actors", "name", "name"),
    "Backdoor": TLOLookupConfig("backdoors", "name", "name"),
    "Campaign": TLOLookupConfig("campaigns", "name", "name"),
    "Certificate": TLOLookupConfig("certificates", "filename", "filename"),
    "Domain": TLOLookupConfig("domains", "domain", "domain"),
    "Email": TLOLookupConfig("emails", "subject", "subject"),
    "Event": TLOLookupConfig("events", "title", "title"),
    "Exploit": TLOLookupConfig("exploits", "name", "name"),
    "Indicator": TLOLookupConfig("indicators", "value", "value"),
    "IP": TLOLookupConfig("ips", "ip", "ip"),
    "PCAP": TLOLookupConfig("pcaps", "filename", "filename"),
    "RawData": TLOLookupConfig("raw_data", "title", "title"),
    "Sample": TLOLookupConfig("sample", "filename", "filename"),
    "Screenshot": TLOLookupConfig("screenshots", "filename", "filename"),
    "Signature": TLOLookupConfig("signatures", "title", "title"),
    "Target": TLOLookupConfig("targets", "email_address", "email_address"),
}

BUCKET_TYPE_FIELDS = (
    "Actor",
    "Backdoor",
    "Campaign",
    "Certificate",
    "Domain",
    "Email",
    "Event",
    "Exploit",
    "Indicator",
    "IP",
    "PCAP",
    "RawData",
    "Sample",
    "Signature",
    "Target",
)

CAMPAIGN_COUNT_FIELDS = (
    "actor_count",
    "backdoor_count",
    "domain_count",
    "email_count",
    "event_count",
    "exploit_count",
    "indicator_count",
    "ip_count",
    "pcap_count",
    "sample_count",
)


def get_tlo_lookup_config(tlo_type: str) -> TLOLookupConfig | None:
    """Return lookup metadata for a TLO type, if supported."""

    return TLO_LOOKUP_CONFIG.get(tlo_type)


def iter_tlo_lookup_configs(
    types: Iterable[str] | None = None,
) -> Iterable[tuple[str, TLOLookupConfig]]:
    """Iterate supported TLO types, optionally filtered to a subset."""

    if types is None:
        return TLO_LOOKUP_CONFIG.items()
    return (
        (tlo_type, config) for tlo_type, config in TLO_LOOKUP_CONFIG.items() if tlo_type in types
    )


def _extract_field(record: dict[str, Any], field_name: str) -> Any:
    """Read a possibly dotted field path from a raw Mongo document."""

    current: Any = record
    for part in field_name.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def display_value_for_record(record: dict[str, Any], tlo_type: str) -> str:
    """Get the configured display value for a raw TLO document."""

    config = get_tlo_lookup_config(tlo_type)
    if config is None:
        return str(record.get("_id", ""))
    display = _extract_field(record, config.display_field)
    if display is None or display == "":
        return str(record.get("_id", ""))
    return str(display)


def get_tlo_record_by_type(
    tlo_type: str,
    record_id: str,
    *,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Fetch a single TLO document by type and id."""

    config = get_tlo_lookup_config(tlo_type)
    if config is None:
        return None
    return get_tlo_record(config.collection_name, record_id, filters=filters)


def search_tlo_records(
    tlo_type: str,
    search_value: str,
    *,
    filters: dict[str, Any] | None = None,
    limit: int = 10,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Search a TLO collection by its configured search field."""

    config = get_tlo_lookup_config(tlo_type)
    if config is None:
        return []

    query = combine_filters(
        filters or {},
        build_contains_filter(config.search_field, search_value),
    )
    return list_tlo_records(
        config.collection_name,
        filters=query,
        limit=limit,
        offset=offset,
        allowed_sort_fields={},
    )


def list_tagged_tlo_records(
    tlo_type: str,
    tag: str,
    *,
    filters: dict[str, Any] | None = None,
    limit: int = 25,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List TLO documents with a matching bucket-list tag."""

    config = get_tlo_lookup_config(tlo_type)
    if config is None:
        return []

    query = combine_filters(filters or {}, {"bucket_list": tag})
    return list_tlo_records(
        config.collection_name,
        filters=query,
        limit=limit,
        offset=offset,
        allowed_sort_fields={},
    )


def count_tlo_records_by_type(
    tlo_type: str,
    *,
    filters: dict[str, Any] | None = None,
) -> int:
    """Count TLO documents for a configured type."""

    config = get_tlo_lookup_config(tlo_type)
    if config is None:
        return 0
    return count_tlo_records(config.collection_name, filters=filters)


def get_recent_tlo_record(
    tlo_type: str,
    *,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Fetch the most recently modified document for a TLO type."""

    config = get_tlo_lookup_config(tlo_type)
    if config is None:
        return None

    records = list_tlo_records(
        config.collection_name,
        filters=filters,
        limit=1,
        allowed_sort_fields={},
    )
    return records[0] if records else None


def list_bucket_summary_records() -> list[dict[str, Any]]:
    """List raw bucket-list summary records ordered by name."""

    return list(get_tlo_collection("bucket_lists").find({}).sort("name", 1))


def get_campaign_top_records(
    *,
    filters: dict[str, Any] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """List recent campaigns for top-campaign summarization."""

    return list(
        get_tlo_collection("campaigns").find(filters or {}).sort("modified", -1).limit(limit)
    )


def association_count_for_campaign(record: dict[str, Any]) -> int:
    """Estimate the number of objects associated to a campaign."""

    total = sum(int(record.get(field, 0) or 0) for field in CAMPAIGN_COUNT_FIELDS)
    if total:
        return total
    relationships = record.get("relationships", []) or []
    return len(relationships)


def find_comment_records(
    obj_type: str,
    obj_id: str,
) -> list[dict[str, Any]]:
    """List raw comment documents for a TLO."""

    object_id = coerce_object_id(obj_id)
    if object_id is None:
        return []
    return list(
        get_tlo_collection("comments")
        .find({"obj_id": object_id, "obj_type": obj_type})
        .sort("date", 1)
    )
