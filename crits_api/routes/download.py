"""REST endpoint for streaming file downloads from GridFS."""

import logging
from collections.abc import Generator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from crits_api.auth.session import (
    get_user_from_session,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["download"])

CHUNK_SIZE = 64 * 1024  # 64KB chunks


@router.get("/download/{md5}", response_model=None)
async def download_sample(request: Request, md5: str) -> StreamingResponse | JSONResponse:
    """
    Stream a sample file from GridFS by MD5 hash.

    Authentication: Django session cookie
    Permission: Sample.read
    """
    from crits.samples.sample import Sample

    # Authenticate
    user = await get_user_from_session(request)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "Authentication required"})

    # Check permission
    if not user.has_access_to("Sample.read") and not getattr(user, "is_superuser", False):
        return JSONResponse(status_code=403, content={"detail": "Permission denied"})

    # Validate MD5 format
    if not md5 or len(md5) != 32:
        return JSONResponse(status_code=400, content={"detail": "Invalid MD5 hash"})

    md5 = md5.lower()

    # Find the sample
    try:
        sample = Sample.objects(md5=md5).first()
    except Exception as e:
        logger.error("Error looking up sample %s: %s", md5, e)
        return JSONResponse(status_code=500, content={"detail": "Database error"})

    if not sample:
        return JSONResponse(status_code=404, content={"detail": "Sample not found"})

    # Check source/TLP access
    if (
        not getattr(user, "is_superuser", False)
        and hasattr(user, "check_source_tlp")
        and not user.check_source_tlp(sample)
    ):
        return JSONResponse(
            status_code=403, content={"detail": "Access denied by source/TLP policy"}
        )

    # Ensure GridFS file data exists
    filedata = getattr(sample, "filedata", None)
    if filedata is None or getattr(filedata, "grid_id", None) is None:
        # Try to discover binary
        try:
            sample.discover_binary()
            filedata = sample.filedata
            if getattr(filedata, "grid_id", None) is None:
                return JSONResponse(
                    status_code=404, content={"detail": "File data not found in GridFS"}
                )
        except Exception:
            return JSONResponse(
                status_code=404, content={"detail": "File data not found in GridFS"}
            )

    filename = sample.filename or f"{md5}.bin"
    mimetype = sample.mimetype or "application/octet-stream"

    def _stream() -> Generator[bytes, None, None]:
        """Generator that yields file chunks from GridFS."""
        try:
            filedata.seek(0)
            while True:
                chunk = filedata.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk
        except Exception as e:
            logger.error("Error streaming file %s: %s", md5, e)

    return StreamingResponse(
        _stream(),
        media_type=mimetype,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
