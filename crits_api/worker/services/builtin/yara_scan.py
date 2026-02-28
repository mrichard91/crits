"""YARA scan service — scans files against YARA rules.

Opt-in only (run_on_triage=False). Gracefully handles missing yara-python.
"""

import logging
import os
from collections.abc import Iterable
from dataclasses import dataclass

from crits_api.worker.services.base import (
    AnalysisContext,
    AnalysisService,
    ServiceConfig,
    config_field,
)
from crits_api.worker.services.registry import register_service

logger = logging.getLogger(__name__)

try:
    import yara

    _YARA_AVAILABLE = True
except ImportError:
    _YARA_AVAILABLE = False
    logger.info("yara-python not installed — YaraScanService will be unavailable")


@dataclass
class YaraScanConfig(ServiceConfig):
    """Configuration for the YARA scan service."""

    rules_directories: str = config_field(
        default="/app/yara_rules,/opt/yara_rules",
        type="str",
        description="Comma-separated list of directories containing .yar/.yara rule files",
        required=True,
    )
    timeout: int = config_field(
        default=60,
        type="int",
        description="Timeout in seconds for each YARA rule compilation/scan",
    )
    recursive: bool = config_field(
        default=True,
        type="bool",
        description="Recursively scan subdirectories for rule files",
    )


@register_service
class YaraScanService(AnalysisService):
    name = "yara_scan"
    version = "1.1.0"
    description = "Scan files against YARA rules"
    supported_types = ["Sample", "PCAP", "RawData"]
    run_on_triage = False
    config_class = YaraScanConfig

    def validate_target(self, context: AnalysisContext) -> bool:
        if not _YARA_AVAILABLE:
            context.warning("yara-python is not installed, skipping YARA scan")
            return False
        if not self.supports_type(context.obj_type):
            return False
        if not hasattr(context.obj, "filedata") or not context.obj.filedata:
            context.info("No file data available, skipping YARA scan")
            return False
        return True

    def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
        cfg: YaraScanConfig = config if isinstance(config, YaraScanConfig) else YaraScanConfig()

        if not _YARA_AVAILABLE:
            context.error_log("yara-python is not installed")
            context.status = "error"
            return

        data = context.get_file_data()
        if not data:
            context.error_log("Could not read file data")
            context.status = "error"
            return

        # Parse rules directories from config
        rules_dirs = [
            d.strip()
            for d in str(cfg.rules_directories).split(",")
            if d.strip() and os.path.isdir(d.strip())
        ]
        if not rules_dirs:
            context.info("No YARA rules directories found")
            return

        timeout = int(cfg.timeout) if cfg.timeout else 60

        total_matches = 0
        for rules_dir in rules_dirs:
            matches = self._scan_with_rules_dir(
                data, rules_dir, context, recursive=cfg.recursive, timeout=timeout
            )
            total_matches += matches

        context.info(f"YARA scan complete: {total_matches} rule(s) matched")

    def _scan_with_rules_dir(
        self,
        data: bytes,
        rules_dir: str,
        context: AnalysisContext,
        *,
        recursive: bool = True,
        timeout: int = 60,
    ) -> int:
        """Scan data against all .yar/.yara files in a directory."""
        match_count = 0

        walk_iter: Iterable[tuple[str, list[str], list[str]]]
        if recursive:
            walk_iter = os.walk(rules_dir)
        else:
            try:
                entries = os.listdir(rules_dir)
            except OSError:
                return 0
            walk_iter = [(rules_dir, [], entries)]

        for root, _dirs, files in walk_iter:
            for fname in files:
                if not fname.endswith((".yar", ".yara")):
                    continue
                rule_path = os.path.join(root, fname)
                try:
                    rules = yara.compile(filepath=rule_path)
                    matches = rules.match(data=data, timeout=timeout)
                    for match in matches:
                        context.add_result(
                            subtype="yara_match",
                            result=str(match.rule),
                            data={
                                "rule_file": fname,
                                "tags": list(match.tags),
                                "meta": {k: str(v) for k, v in match.meta.items()},
                            },
                        )
                        match_count += 1
                except Exception as e:
                    context.warning(f"Failed to compile/scan {fname}: {e}")

        return match_count
