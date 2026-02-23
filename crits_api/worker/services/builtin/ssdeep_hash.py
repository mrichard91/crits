"""SSDeep fuzzy hash service.

Calculates ssdeep fuzzy hashes for file-based TLOs.
Gracefully handles missing pydeep library.
"""

import logging

from crits_api.worker.services.base import AnalysisContext, AnalysisService, ServiceConfig
from crits_api.worker.services.registry import register_service

logger = logging.getLogger(__name__)

try:
    import pydeep

    _PYDEEP_AVAILABLE = True
except ImportError:
    _PYDEEP_AVAILABLE = False
    logger.info("pydeep not installed — SSDeepHashService will be unavailable")


@register_service
class SSDeepHashService(AnalysisService):
    name = "ssdeep"
    version = "1.0.0"
    description = "Calculate ssdeep fuzzy hash"
    supported_types = ["Sample", "PCAP", "Certificate"]
    run_on_triage = True

    def validate_target(self, context: AnalysisContext) -> bool:
        if not _PYDEEP_AVAILABLE:
            context.warning("pydeep is not installed, skipping ssdeep hash")
            return False
        if not self.supports_type(context.obj_type):
            return False
        if not hasattr(context.obj, "filedata") or not context.obj.filedata:
            context.info("No file data available, skipping ssdeep hash")
            return False
        return True

    def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
        if not _PYDEEP_AVAILABLE:
            context.error_log("pydeep is not installed")
            context.status = "error"
            return

        data = context.get_file_data()
        if not data:
            context.error_log("Could not read file data")
            context.status = "error"
            return

        context.info(f"Calculating ssdeep hash for {len(data)} bytes")

        try:
            fuzzy_hash = pydeep.hash_buf(data)
            if isinstance(fuzzy_hash, bytes):
                fuzzy_hash = fuzzy_hash.decode("utf-8", errors="replace")
            context.add_result(subtype="ssdeep", result=fuzzy_hash)
            context.info("ssdeep hash calculation complete")
        except Exception as e:
            context.error_log(f"ssdeep hash calculation failed: {e}")
            context.status = "error"
