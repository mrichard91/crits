"""FileType analysis service — libmagic detection, MIME type, file size."""

import logging

from crits_api.worker.services.base import AnalysisContext, AnalysisService, ServiceConfig
from crits_api.worker.services.registry import register_service

logger = logging.getLogger(__name__)


@register_service
class FileTypeService(AnalysisService):
    name = "filetype"
    version = "1.0.0"
    description = "Detect file type using libmagic, MIME type, and file size"
    supported_types = ["Sample", "PCAP", "Certificate"]
    run_on_triage = True

    def validate_target(self, context: AnalysisContext) -> bool:
        """Require file data to be present."""
        if not self.supports_type(context.obj_type):
            return False
        if not hasattr(context.obj, "filedata") or not context.obj.filedata:
            context.info("No file data available, skipping filetype analysis")
            return False
        return True

    def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
        data = context.get_file_data()
        if not data:
            context.error_log("Could not read file data")
            context.status = "error"
            return

        context.info(f"Analyzing file ({len(data)} bytes)")

        # File size
        context.add_result(
            subtype="file_size",
            result=str(len(data)),
            data={"bytes": len(data)},
        )

        # libmagic file type
        try:
            import magic

            file_type = magic.from_buffer(data)
            context.add_result(subtype="filetype", result=file_type)
        except Exception as e:
            context.warning(f"libmagic detection failed: {e}")

        # MIME type
        try:
            import magic

            mime_type = magic.from_buffer(data, mime=True)
            context.add_result(subtype="mimetype", result=mime_type)
        except Exception as e:
            context.warning(f"MIME type detection failed: {e}")

        context.info("File type analysis complete")
