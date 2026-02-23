"""YARA scan service — scans files against YARA rules.

Opt-in only (run_on_triage=False). Gracefully handles missing yara-python.
"""

import logging
import os

from crits_api.worker.services.base import AnalysisContext, AnalysisService, ServiceConfig
from crits_api.worker.services.registry import register_service

logger = logging.getLogger(__name__)

try:
    import yara

    _YARA_AVAILABLE = True
except ImportError:
    _YARA_AVAILABLE = False
    logger.info("yara-python not installed — YaraScanService will be unavailable")


@register_service
class YaraScanService(AnalysisService):
    name = "yara_scan"
    version = "1.0.0"
    description = "Scan files against YARA rules"
    supported_types = ["Sample", "PCAP", "RawData"]
    run_on_triage = False

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
        if not _YARA_AVAILABLE:
            context.error_log("yara-python is not installed")
            context.status = "error"
            return

        data = context.get_file_data()
        if not data:
            context.error_log("Could not read file data")
            context.status = "error"
            return

        # Look for YARA rules in configured directories
        rules_dirs = self._get_rules_dirs()
        if not rules_dirs:
            context.info("No YARA rules directories configured")
            return

        total_matches = 0
        for rules_dir in rules_dirs:
            matches = self._scan_with_rules_dir(data, rules_dir, context)
            total_matches += matches

        context.info(f"YARA scan complete: {total_matches} rule(s) matched")

    def _get_rules_dirs(self) -> list[str]:
        """Get YARA rules directories from environment or defaults."""
        env_dirs = os.environ.get("YARA_RULES_DIRS", "")
        if env_dirs:
            return [
                d.strip() for d in env_dirs.split(",") if d.strip() and os.path.isdir(d.strip())
            ]

        # Default locations
        defaults = ["/app/yara_rules", "/opt/yara_rules"]
        return [d for d in defaults if os.path.isdir(d)]

    def _scan_with_rules_dir(
        self,
        data: bytes,
        rules_dir: str,
        context: AnalysisContext,
    ) -> int:
        """Scan data against all .yar/.yara files in a directory."""
        match_count = 0

        for root, _dirs, files in os.walk(rules_dir):
            for fname in files:
                if not fname.endswith((".yar", ".yara")):
                    continue
                rule_path = os.path.join(root, fname)
                try:
                    rules = yara.compile(filepath=rule_path)
                    matches = rules.match(data=data)
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
