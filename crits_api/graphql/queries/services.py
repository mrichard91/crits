"""Service queries for CRITs GraphQL API."""

import dataclasses
import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_authenticated
from crits_api.db.service_records import find_service_records, get_service_record

logger = logging.getLogger(__name__)


@strawberry.type
class ServiceConfigOption:
    """A single configuration option for a service."""

    key: str
    value: str
    default: str
    description: str
    config_type: str  # "str", "int", "bool"
    required: bool
    private: bool


@strawberry.type
class ServiceDetail:
    """Full detail about a service (modern or legacy)."""

    name: str
    version: str
    description: str
    enabled: bool
    run_on_triage: bool
    supported_types: list[str]
    is_modern: bool
    config_options: list[ServiceConfigOption]


@strawberry.type
class ServiceQueries:
    """Service-related queries."""

    @strawberry.field(description="Get all services with full detail")
    @require_authenticated
    def services(self, info: Info) -> list[ServiceDetail]:
        """List all services (modern registry + legacy DB) with full detail."""
        services: list[ServiceDetail] = []
        seen_names: set[str] = set()

        # Modern registered services
        try:
            from crits_api.worker.services.registry import (
                ensure_services_registered,
                get_all_services,
            )

            ensure_services_registered()
            for name, cls in get_all_services().items():
                # Check for a persisted DB record with admin overrides
                db_record = get_service_record(name)

                enabled = db_record.enabled if db_record and db_record.enabled is not None else True
                run_on_triage = (
                    db_record.run_on_triage
                    if db_record and db_record.run_on_triage is not None
                    else cls.run_on_triage
                )

                # Extract config options from config_class dataclass fields
                config_options = _extract_config_options(
                    cls.config_class,
                    db_record.config if db_record else None,
                )

                services.append(
                    ServiceDetail(
                        name=cls.name,
                        version=cls.version,
                        description=cls.description,
                        enabled=enabled,
                        run_on_triage=run_on_triage,
                        supported_types=list(cls.supported_types),
                        is_modern=True,
                        config_options=config_options,
                    )
                )
                seen_names.add(name)
        except Exception as e:
            logger.debug(f"Could not load modern services: {e}")

        # Legacy DB services (not already covered by modern)
        try:
            for svc in find_service_records():
                if svc.name in seen_names:
                    continue

                legacy_opts: list[ServiceConfigOption] = []
                if svc.config:
                    for key, val in svc.config.items():
                        legacy_opts.append(
                            ServiceConfigOption(
                                key=key,
                                value=str(val) if val is not None else "",
                                default="",
                                description="",
                                config_type="str",
                                required=False,
                                private=False,
                            )
                        )

                services.append(
                    ServiceDetail(
                        name=svc.name,
                        version=svc.version,
                        description=svc.description,
                        enabled=bool(svc.enabled) if svc.enabled is not None else False,
                        run_on_triage=bool(svc.run_on_triage)
                        if svc.run_on_triage is not None
                        else False,
                        supported_types=list(svc.supported_types or []),
                        is_modern=False,
                        config_options=legacy_opts,
                    )
                )
        except Exception as e:
            logger.error(f"Error listing legacy services: {e}")

        return services


def _extract_config_options(
    config_class: type,
    db_config: dict[str, object] | None,
) -> list[ServiceConfigOption]:
    """Extract config options from a dataclass config_class."""
    options: list[ServiceConfigOption] = []
    if not dataclasses.is_dataclass(config_class):
        return options

    # Get persisted config values from DB record
    db_config_values: dict[str, str] = {}
    if db_config:
        for key, val in db_config.items():
            if val is not None:
                db_config_values[key] = str(val)

    for field in dataclasses.fields(config_class):
        default_val = ""
        if field.default is not dataclasses.MISSING:
            default_val = str(field.default)
        elif field.default_factory is not dataclasses.MISSING:
            default_val = str(field.default_factory())

        current_val = db_config_values.get(field.name, default_val)
        meta: dict[str, object] = dict(field.metadata) if field.metadata else {}

        options.append(
            ServiceConfigOption(
                key=field.name,
                value=current_val,
                default=default_val,
                description=str(meta.get("description", "")),
                config_type=str(meta.get("config_type", "str")),
                required=bool(meta.get("required", False)),
                private=bool(meta.get("private", False)),
            )
        )

    return options
