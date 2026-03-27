"""Analysis result queries for CRITs GraphQL API."""

import logging
from typing import Any, cast

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_authenticated
from crits_api.db.analysis_records import AnalysisRecord, find_analysis_records, get_analysis_record

logger = logging.getLogger(__name__)


@strawberry.type
class AnalysisResultLogType:
    """Log entry from a service execution."""

    message: str = ""
    level: str = ""
    datetime: str = ""


@strawberry.type
class AnalysisResultType:
    """Result of a service execution on a TLO."""

    id: str
    analysis_id: str
    service_name: str = ""
    version: str = ""
    object_type: str = ""
    object_id: str = ""
    analyst: str = ""
    status: str = ""
    start_date: str = ""
    finish_date: str = ""
    results: list[strawberry.scalars.JSON] = strawberry.field(default_factory=list)
    log: list[AnalysisResultLogType] = strawberry.field(default_factory=list)

    @classmethod
    def from_record(cls, ar: AnalysisRecord) -> "AnalysisResultType":
        """Create AnalysisResultType from a normalized analysis record."""
        return cls(
            id=ar.id,
            analysis_id=ar.analysis_id,
            service_name=ar.service_name or "",
            version=ar.version or "",
            object_type=ar.object_type or "",
            object_id=ar.object_id or "",
            analyst=ar.analyst or "",
            status=ar.status or "",
            start_date=ar.start_date or "",
            finish_date=ar.finish_date or "",
            results=cast(list[strawberry.scalars.JSON], list(ar.results)),
            log=[
                AnalysisResultLogType(
                    message=entry.message,
                    level=entry.level,
                    datetime=entry.datetime,
                )
                for entry in ar.log
            ],
        )


@strawberry.type
class AnalysisResultQueries:
    """Queries for analysis results."""

    @strawberry.field(description="Get analysis results for a TLO")
    @require_authenticated
    def analysis_results(
        self,
        info: Info,
        obj_type: str,
        obj_id: str,
        service_name: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AnalysisResultType]:
        """
        Get analysis results for a specific TLO.

        Args:
            obj_type: The TLO type (e.g., "Sample", "Indicator")
            obj_id: The ObjectId of the TLO
            service_name: Optional filter by service name
            status: Optional filter by status
            limit: Maximum number of results (default 50, max 200)
            offset: Number of results to skip

        Returns:
            List of analysis results
        """
        limit = min(limit, 200)

        try:
            query: dict[str, Any] = {
                "object_type": obj_type,
                "object_id": str(obj_id),
            }

            if service_name:
                query["service_name"] = service_name

            if status:
                query["status"] = status

            results = find_analysis_records(query, limit=limit, offset=offset)
            return [AnalysisResultType.from_record(ar) for ar in results]

        except Exception as e:
            logger.error(f"Error fetching analysis results: {e}")
            return []

    @strawberry.field(description="Get a single analysis result by analysis_id")
    @require_authenticated
    def analysis_result(
        self,
        info: Info,
        analysis_id: str,
    ) -> AnalysisResultType | None:
        """
        Get a single analysis result by its analysis_id (UUID).

        Args:
            analysis_id: The UUID of the analysis record

        Returns:
            The analysis result if found, None otherwise
        """
        try:
            ar = get_analysis_record(analysis_id)
            if ar:
                return AnalysisResultType.from_record(ar)
            return None

        except Exception as e:
            logger.error(f"Error fetching analysis result {analysis_id}: {e}")
            return None
