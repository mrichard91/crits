"""Hash calculation service — MD5, SHA-1, SHA-256."""

import hashlib
import logging

from crits_api.worker.services.base import AnalysisContext, AnalysisService, ServiceConfig
from crits_api.worker.services.registry import register_service

logger = logging.getLogger(__name__)


@register_service
class HashCalculationService(AnalysisService):
    name = "hashes"
    version = "1.0.0"
    description = "Calculate MD5, SHA-1, and SHA-256 hashes"
    supported_types = ["Sample", "PCAP", "Certificate"]
    run_on_triage = True

    def validate_target(self, context: AnalysisContext) -> bool:
        if not self.supports_type(context.obj_type):
            return False
        if not hasattr(context.obj, "filedata") or not context.obj.filedata:
            context.info("No file data available, skipping hash calculation")
            return False
        return True

    def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
        data = context.get_file_data()
        if not data:
            context.error_log("Could not read file data")
            context.status = "error"
            return

        context.info(f"Calculating hashes for {len(data)} bytes")

        md5 = hashlib.md5(data).hexdigest()
        sha1 = hashlib.sha1(data).hexdigest()
        sha256 = hashlib.sha256(data).hexdigest()

        context.add_result(subtype="md5", result=md5)
        context.add_result(subtype="sha1", result=sha1)
        context.add_result(subtype="sha256", result=sha256)

        context.info("Hash calculation complete")
