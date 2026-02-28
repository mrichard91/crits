"""Analysis service base class, context, and configuration."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


# -- Configuration field helper ------------------------------------------------


def config_field(
    default: Any = dataclass,  # sentinel — replaced below
    *,
    type: str = "str",
    description: str = "",
    required: bool = False,
    private: bool = False,
    default_factory: Any = dataclass,  # sentinel
) -> Any:
    """Create a dataclass field with service-config metadata.

    Mirrors the legacy ``ServiceConfigOption`` constructor arguments:

    * *type*: ``"str"``, ``"int"``, ``"bool"`` — drives UI widget selection.
    * *description*: human-readable help text shown in the admin UI.
    * *required*: whether the field must be set before the service is usable.
    * *private*: if ``True`` the value is masked in the UI (API keys, etc.).

    Usage::

        @dataclass
        class MyConfig(ServiceConfig):
            api_key: str = config_field(default="", type="str",
                                        description="API key for ...",
                                        required=True, private=True)
            timeout: int = config_field(default=30, type="int",
                                        description="Request timeout in seconds")
    """
    metadata = {
        "config_type": type,
        "description": description,
        "required": required,
        "private": private,
    }

    _sentinel = dataclass  # reuse the class object as an "unset" marker

    if default is not _sentinel and default_factory is not _sentinel:
        raise ValueError("Cannot specify both default and default_factory")

    if default_factory is not _sentinel:
        return field(default_factory=default_factory, metadata=metadata)
    if default is not _sentinel:
        return field(default=default, metadata=metadata)
    # No default — the caller must provide a value
    return field(metadata=metadata)


@dataclass
class ServiceConfig:
    """Base configuration for analysis services.

    Subclass and add fields (optionally using ``config_field``) to declare
    service-specific configuration.
    """

    def to_dict(self) -> dict[str, Any]:
        """Serialize config to dict for storage."""
        from dataclasses import asdict

        return asdict(self)


class AnalysisContext:
    """Context passed to service run() — accumulates results and log entries.

    Services add results via add_result() and log via info()/warning()/etc.
    The execution pipeline reads results/log_entries after run() returns.
    """

    def __init__(
        self,
        obj: Any,
        obj_type: str,
        obj_id: str,
        username: str,
        analysis_id: str,
    ) -> None:
        self.obj = obj
        self.obj_type = obj_type
        self.obj_id = obj_id
        self.username = username
        self.analysis_id = analysis_id
        self.results: list[dict[str, Any]] = []
        self.log_entries: list[dict[str, str]] = []
        self.status: str = "started"

    def add_result(
        self,
        subtype: str,
        result: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Add an analysis result."""
        entry: dict[str, Any] = {"subtype": subtype, "result": result}
        if data:
            entry.update(data)
        self.results.append(entry)

    def get_file_data(self) -> bytes | None:
        """Read file data from GridFS for Sample/PCAP objects."""
        try:
            if hasattr(self.obj, "filedata") and self.obj.filedata:
                self.obj.filedata.seek(0)
                return self.obj.filedata.read()
        except Exception as e:
            self.error_log(f"Failed to read file data: {e}")
        return None

    # --- Logging helpers ---

    def _log(self, level: str, msg: str) -> None:
        self.log_entries.append(
            {
                "level": level,
                "message": msg,
                "datetime": str(datetime.now()),
            }
        )

    def debug(self, msg: str) -> None:
        """Add a debug log entry."""
        self._log("debug", msg)

    def info(self, msg: str) -> None:
        """Add an info log entry."""
        self._log("info", msg)

    def warning(self, msg: str) -> None:
        """Add a warning log entry."""
        self._log("warning", msg)

    def error_log(self, msg: str) -> None:
        """Add an error log entry."""
        self._log("error", msg)


class AnalysisService(ABC):
    """Abstract base class for modern CRITs analysis services.

    Subclasses must define class attributes and implement run().
    """

    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    supported_types: list[str] = ["all"]
    run_on_triage: bool = False
    config_class: type[ServiceConfig] = ServiceConfig

    @abstractmethod
    def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
        """Execute the analysis service.

        Implementations should call context.add_result() and context.info() etc.
        to record results and log entries. Do NOT write to the DB directly.
        """
        ...

    def validate_target(self, context: AnalysisContext) -> bool:
        """Check whether this service can process the given object.

        Override to add custom validation (e.g., require filedata).
        Returns True if the target is valid.
        """
        return self.supports_type(context.obj_type)

    @classmethod
    def supports_type(cls, obj_type: str) -> bool:
        """Check if this service supports the given TLO type."""
        if "all" in cls.supported_types:
            return True
        return obj_type in cls.supported_types
