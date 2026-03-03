"""PE file analysis service — parse PE headers, sections, imports, and exports.

Requires optional ``pefile`` dependency. Gracefully handles missing library.
"""

import logging
from datetime import UTC, datetime

from crits_api.worker.services.base import AnalysisContext, AnalysisService, ServiceConfig
from crits_api.worker.services.registry import register_service

logger = logging.getLogger(__name__)

try:
    import pefile

    _PEFILE_AVAILABLE = True
except ImportError:
    _PEFILE_AVAILABLE = False
    logger.info("pefile not installed — PEInfoService will be unavailable")


@register_service
class PEInfoService(AnalysisService):
    name = "peinfo"
    version = "1.0.0"
    description = "Parse PE file headers, sections, imports, and exports"
    supported_types = ["Sample"]
    run_on_triage = False

    def validate_target(self, context: AnalysisContext) -> bool:
        if not _PEFILE_AVAILABLE:
            context.warning("pefile is not installed, skipping PE analysis")
            return False
        if not self.supports_type(context.obj_type):
            return False
        if not hasattr(context.obj, "filedata") or not context.obj.filedata:
            context.info("No file data available, skipping PE analysis")
            return False
        return True

    def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
        if not _PEFILE_AVAILABLE:
            context.error_log("pefile is not installed")
            context.status = "error"
            return

        data = context.get_file_data()
        if not data:
            context.error_log("Could not read file data")
            context.status = "error"
            return

        # Check MZ header
        if len(data) < 2 or data[:2] != b"MZ":
            context.info("Not a PE file (missing MZ header), skipping")
            return

        try:
            pe = pefile.PE(data=data, fast_load=False)
        except pefile.PEFormatError as e:
            context.warning(f"Invalid PE format: {e}")
            return
        except Exception as e:
            context.error_log(f"Failed to parse PE file: {e}")
            context.status = "error"
            return

        context.info(f"Analyzing PE file ({len(data)} bytes)")

        # Machine type
        machine = pefile.MACHINE_TYPE.get(
            pe.FILE_HEADER.Machine,
            f"Unknown (0x{pe.FILE_HEADER.Machine:04X})",
        )
        context.add_result(subtype="machine_type", result=str(machine))

        # Compile timestamp
        try:
            ts = pe.FILE_HEADER.TimeDateStamp
            compile_time = datetime.fromtimestamp(ts, tz=UTC).isoformat()
            context.add_result(
                subtype="compile_timestamp",
                result=compile_time,
                data={"raw": ts},
            )
        except Exception:
            pass

        # Entry point
        context.add_result(
            subtype="entry_point",
            result=f"0x{pe.OPTIONAL_HEADER.AddressOfEntryPoint:08X}",
        )

        # Sections
        for section in pe.sections:
            try:
                name = section.Name.rstrip(b"\x00").decode("utf-8", errors="replace")
            except Exception:
                name = "<unknown>"
            context.add_result(
                subtype="section",
                result=name,
                data={
                    "virtual_address": f"0x{section.VirtualAddress:08X}",
                    "virtual_size": section.Misc_VirtualSize,
                    "raw_size": section.SizeOfRawData,
                    "entropy": round(section.get_entropy(), 4),
                },
            )

        # Imports
        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                dll_name = entry.dll.decode("utf-8", errors="replace") if entry.dll else "<unknown>"
                functions = []
                for imp in entry.imports:
                    if imp.name:
                        functions.append(imp.name.decode("utf-8", errors="replace"))
                    else:
                        functions.append(f"ordinal_{imp.ordinal}")
                context.add_result(
                    subtype="import_dll",
                    result=dll_name,
                    data={"functions": functions, "count": len(functions)},
                )

        # Exports
        if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
            for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                name = (
                    exp.name.decode("utf-8", errors="replace")
                    if exp.name
                    else f"ordinal_{exp.ordinal}"
                )
                context.add_result(
                    subtype="export",
                    result=name,
                    data={"ordinal": exp.ordinal},
                )

        pe.close()
        context.info("PE analysis complete")
