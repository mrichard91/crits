"""String extraction service — ASCII and Unicode strings from binary data."""

import logging
import re
from dataclasses import dataclass

from crits_api.worker.services.base import (
    AnalysisContext,
    AnalysisService,
    ServiceConfig,
    config_field,
)
from crits_api.worker.services.registry import register_service

logger = logging.getLogger(__name__)


@dataclass
class StringsConfig(ServiceConfig):
    """Configuration for the strings extraction service."""

    min_length: int = config_field(
        default=4,
        type="int",
        description="Minimum string length to extract",
        required=True,
    )
    max_results: int = config_field(
        default=1000,
        type="int",
        description="Maximum number of strings to return",
    )


@register_service
class StringsService(AnalysisService):
    name = "strings"
    version = "1.0.0"
    description = "Extract ASCII and Unicode strings from binary data"
    supported_types = ["Sample", "PCAP", "RawData"]
    run_on_triage = False
    config_class = StringsConfig

    def validate_target(self, context: AnalysisContext) -> bool:
        if not self.supports_type(context.obj_type):
            return False
        if not hasattr(context.obj, "filedata") or not context.obj.filedata:
            context.info("No file data available, skipping string extraction")
            return False
        return True

    def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
        cfg: StringsConfig = config if isinstance(config, StringsConfig) else StringsConfig()

        data = context.get_file_data()
        if not data:
            context.error_log("Could not read file data")
            context.status = "error"
            return

        min_len = int(cfg.min_length) if cfg.min_length else 4
        max_results = int(cfg.max_results) if cfg.max_results else 1000

        context.info(f"Extracting strings (min_length={min_len}) from {len(data)} bytes")

        count = 0

        # ASCII strings: printable characters
        ascii_pattern = re.compile(rb"[ -~]{%d,}" % min_len)
        for match in ascii_pattern.finditer(data):
            if count >= max_results:
                break
            value = match.group().decode("ascii", errors="replace")
            context.add_result(
                subtype="ascii_string",
                result=value,
                data={"offset": match.start(), "length": len(value)},
            )
            count += 1

        # Unicode (UTF-16LE) strings: printable char followed by null byte
        unicode_pattern = re.compile(rb"(?:[ -~]\x00){%d,}" % min_len)
        for match in unicode_pattern.finditer(data):
            if count >= max_results:
                break
            try:
                value = match.group().decode("utf-16-le", errors="replace")
            except Exception:
                continue
            context.add_result(
                subtype="unicode_string",
                result=value,
                data={"offset": match.start(), "length": len(value)},
            )
            count += 1

        context.info(f"String extraction complete: {count} strings found")
