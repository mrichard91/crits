"""Analysis result queries for CRITs GraphQL API."""

import logging
from typing import Any

import strawberry
from strawberry.types import Info

from crits_api.auth.permissions import require_authenticated

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
    def from_model(cls, ar: Any) -> "AnalysisResultType":
        """Create AnalysisResultType from AnalysisResult model."""
        log_entries = []
        if ar.log:
            for entry in ar.log:
                log_entries.append(
                    AnalysisResultLogType(
                        message=getattr(entry, "message", "") or "",
                        level=getattr(entry, "level", "") or "",
                        datetime=getattr(entry, "datetime", "") or "",
                    )
                )

        # Convert results to JSON-serializable list
        results_list: list[Any] = []
        if ar.results:
            for r in ar.results:
                if isinstance(r, dict):
                    results_list.append(r)
                elif hasattr(r, "to_dict"):
                    results_list.append(r.to_dict())
                else:
                    results_list.append({"result": str(r)})

        return cls(
            id=str(ar.id),
            analysis_id=str(ar.analysis_id) if ar.analysis_id else "",
            service_name=ar.service_name or "",
            version=ar.version or "",
            object_type=ar.object_type or "",
            object_id=ar.object_id or "",
            analyst=ar.analyst or "",
            status=ar.status or "",
            start_date=ar.start_date or "",
            finish_date=ar.finish_date or "",
            results=results_list,
            log=log_entries,
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
        from crits.services.analysis_result import AnalysisResult

        limit = min(limit, 200)

        try:
            queryset = AnalysisResult.objects(
                object_type=obj_type,
                object_id=str(obj_id),
            )

            if service_name:
                queryset = queryset.filter(service_name=service_name)

            if status:
                queryset = queryset.filter(status=status)

            queryset = queryset.order_by("-start_date")
            results = queryset.skip(offset).limit(limit)

            return [AnalysisResultType.from_model(ar) for ar in results]

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
        from crits.services.analysis_result import AnalysisResult

        try:
            ar = AnalysisResult.objects(analysis_id=analysis_id).first()
            if ar:
                return AnalysisResultType.from_model(ar)
            return None

        except Exception as e:
            logger.error(f"Error fetching analysis result {analysis_id}: {e}")
            return None
