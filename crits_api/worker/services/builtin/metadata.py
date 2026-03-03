"""Metadata extraction service — image EXIF, OLE2, and OOXML document metadata."""

import logging

from crits_api.worker.services.base import AnalysisContext, AnalysisService, ServiceConfig
from crits_api.worker.services.registry import register_service

logger = logging.getLogger(__name__)


@register_service
class MetadataService(AnalysisService):
    name = "metadata"
    version = "1.1.0"
    description = "Extract image EXIF, OLE2, and OOXML document metadata"
    supported_types = ["Sample"]
    run_on_triage = False

    def validate_target(self, context: AnalysisContext) -> bool:
        if not self.supports_type(context.obj_type):
            return False
        if not hasattr(context.obj, "filedata") or not context.obj.filedata:
            context.info("No file data available, skipping metadata extraction")
            return False
        return True

    def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
        data = context.get_file_data()
        if not data:
            context.error_log("Could not read file data")
            context.status = "error"
            return

        context.info(f"Extracting metadata from {len(data)} bytes")

        found_image = self._extract_image_metadata(data, context)
        found_ole = self._extract_ole_metadata(data, context)
        found_ooxml = self._extract_ooxml_metadata(data, context)

        if not found_image and not found_ole and not found_ooxml:
            context.info("No extractable metadata found in this file")
        else:
            context.info("Metadata extraction complete")

    def _extract_image_metadata(self, data: bytes, context: AnalysisContext) -> bool:
        """Extract image format info and EXIF tags. Returns True if image was parseable."""
        try:
            import io

            from PIL import ExifTags, Image

            img = Image.open(io.BytesIO(data))
        except Exception:
            return False

        context.add_result(
            subtype="image_info",
            result=f"{img.format} {img.size[0]}x{img.size[1]} {img.mode}",
            data={
                "format": img.format or "unknown",
                "width": img.size[0],
                "height": img.size[1],
                "mode": img.mode,
            },
        )

        try:
            exif_data = img.getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, f"Tag_{tag_id}")
                    context.add_result(
                        subtype="exif_tag",
                        result=f"{tag_name}: {value}",
                        data={"tag_id": tag_id, "tag_name": tag_name, "value": str(value)},
                    )
        except Exception as e:
            context.warning(f"EXIF extraction failed: {e}")

        return True

    def _extract_ole_metadata(self, data: bytes, context: AnalysisContext) -> bool:
        """Extract OLE2 document metadata. Returns True if OLE2 was parseable."""
        try:
            import olefile
        except ImportError:
            return False

        if not olefile.isOleFile(data):
            return False

        try:
            ole = olefile.OleFileIO(data)
        except Exception:
            return False

        try:
            meta = ole.get_metadata()
            fields = [
                ("title", meta.title),
                ("author", meta.author),
                ("subject", meta.subject),
                ("keywords", meta.keywords),
                ("comments", meta.comments),
                ("last_saved_by", meta.last_saved_by),
                ("creating_application", meta.creating_application),
                ("create_time", meta.create_time),
                ("last_saved_time", meta.last_saved_time),
                ("company", meta.company),
            ]
            for field_name, value in fields:
                if value:
                    str_val = value.isoformat() if hasattr(value, "isoformat") else str(value)
                    context.add_result(
                        subtype="ole_metadata",
                        result=f"{field_name}: {str_val}",
                        data={"field": field_name, "value": str_val},
                    )

            # List OLE streams
            streams = ole.listdir()
            for stream_path in streams:
                context.add_result(
                    subtype="ole_stream",
                    result="/".join(stream_path),
                )
        except Exception as e:
            context.warning(f"OLE metadata extraction failed: {e}")
        finally:
            ole.close()

        return True

    def _extract_ooxml_metadata(self, data: bytes, context: AnalysisContext) -> bool:
        """Extract OOXML metadata from .docx/.xlsx/.pptx files.

        These are ZIP archives with docProps/core.xml and docProps/app.xml.
        """
        import io
        import zipfile

        if not zipfile.is_zipfile(io.BytesIO(data)):
            return False

        try:
            zf = zipfile.ZipFile(io.BytesIO(data))
        except Exception:
            return False

        # Check for OOXML marker
        if "[Content_Types].xml" not in zf.namelist():
            zf.close()
            return False

        import xml.etree.ElementTree as ET

        found_any = False

        # Core properties (title, author, dates, etc.)
        core_ns = {
            "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/",
        }
        if "docProps/core.xml" in zf.namelist():
            try:
                tree = ET.fromstring(zf.read("docProps/core.xml"))
                core_fields = [
                    ("title", "dc:title"),
                    ("creator", "dc:creator"),
                    ("subject", "dc:subject"),
                    ("description", "dc:description"),
                    ("keywords", "cp:keywords"),
                    ("last_modified_by", "cp:lastModifiedBy"),
                    ("revision", "cp:revision"),
                    ("created", "dcterms:created"),
                    ("modified", "dcterms:modified"),
                    ("category", "cp:category"),
                ]
                for field_name, xpath in core_fields:
                    ns_prefix, tag = xpath.split(":")
                    el = tree.find(f"{{{core_ns[ns_prefix]}}}{tag}")
                    if el is not None and el.text and el.text.strip():
                        context.add_result(
                            subtype="ooxml_core",
                            result=f"{field_name}: {el.text.strip()}",
                            data={"field": field_name, "value": el.text.strip()},
                        )
                        found_any = True
            except Exception as e:
                context.warning(f"OOXML core.xml parse failed: {e}")

        # App properties (application, company, template, etc.)
        app_ns = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
        if "docProps/app.xml" in zf.namelist():
            try:
                tree = ET.fromstring(zf.read("docProps/app.xml"))
                app_fields = [
                    "Application",
                    "AppVersion",
                    "Company",
                    "Template",
                    "TotalTime",
                    "Pages",
                    "Words",
                    "Characters",
                    "Slides",
                    "PresentationFormat",
                ]
                for tag in app_fields:
                    el = tree.find(f"{{{app_ns}}}{tag}")
                    if el is not None and el.text and el.text.strip():
                        field_name = tag.lower()
                        context.add_result(
                            subtype="ooxml_app",
                            result=f"{field_name}: {el.text.strip()}",
                            data={"field": field_name, "value": el.text.strip()},
                        )
                        found_any = True
            except Exception as e:
                context.warning(f"OOXML app.xml parse failed: {e}")

        zf.close()
        return found_any
