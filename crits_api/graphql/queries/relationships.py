"""Relationship queries for CRITs GraphQL API."""

import logging
from typing import Any

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated

logger = logging.getLogger(__name__)


@strawberry.type
class TLOSearchResult:
    """Result from a TLO search."""

    id: str
    display_value: str
    tlo_type: str


# Mapping of TLO type to (model class path, search field, display field)
TLO_TYPE_CONFIG = {
    "Indicator": ("crits.indicators.indicator.Indicator", "value", "value"),
    "Actor": ("crits.actors.actor.Actor", "name", "name"),
    "Backdoor": ("crits.backdoors.backdoor.Backdoor", "name", "name"),
    "Campaign": ("crits.campaigns.campaign.Campaign", "name", "name"),
    "Certificate": ("crits.certificates.certificate.Certificate", "filename", "filename"),
    "Domain": ("crits.domains.domain.Domain", "domain", "domain"),
    "Email": ("crits.emails.email.Email", "subject", "subject"),
    "Event": ("crits.events.event.Event", "title", "title"),
    "Exploit": ("crits.exploits.exploit.Exploit", "name", "name"),
    "IP": ("crits.ips.ip.IP", "ip", "ip"),
    "PCAP": ("crits.pcaps.pcap.PCAP", "filename", "filename"),
    "RawData": ("crits.raw_data.raw_data.RawData", "title", "title"),
    "Sample": ("crits.samples.sample.Sample", "filename", "filename"),
    "Screenshot": ("crits.screenshots.screenshot.Screenshot", "filename", "filename"),
    "Signature": ("crits.signatures.signature.Signature", "title", "title"),
    "Target": ("crits.targets.target.Target", "email_address", "email_address"),
}


def get_model_class(model_path: str) -> Any:
    """Dynamically import and return a model class."""
    parts = model_path.rsplit(".", 1)
    module_path, class_name = parts
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, class_name)


@strawberry.type
class RelationshipQueries:
    """Relationship-related queries."""

    @strawberry.field(description="Get available relationship types")
    @require_authenticated
    def relationship_types(self, info: Info) -> list[str]:
        """
        Get list of available relationship type values.

        Returns:
            Sorted list of relationship type strings
        """
        from crits.vocabulary.relationships import RelationshipTypes

        try:
            return RelationshipTypes.values(sort=True)
        except Exception as e:
            logger.error(f"Error getting relationship types: {e}")
            return []

    @strawberry.field(description="Search for TLOs by type and value")
    @require_authenticated
    def search_tlos(
        self,
        info: Info,
        tlo_type: str,
        search_value: str,
        limit: int = 10,
    ) -> list[TLOSearchResult]:
        """
        Search for TLOs by type and display value.

        Args:
            tlo_type: The TLO type to search (e.g., "Indicator", "Domain")
            search_value: The value to search for (case-insensitive contains)
            limit: Maximum number of results (default 10, max 25)

        Returns:
            List of matching TLOs with id and display value
        """
        ctx: GraphQLContext = info.context
        limit = min(limit, 25)

        if tlo_type not in TLO_TYPE_CONFIG:
            logger.warning(f"Unknown TLO type: {tlo_type}")
            return []

        if not search_value or len(search_value) < 2:
            return []

        model_path, search_field, display_field = TLO_TYPE_CONFIG[tlo_type]

        try:
            model_class = get_model_class(model_path)
            queryset = model_class.objects

            # Apply source/TLP filtering unless superuser
            if not ctx.is_superuser:
                source_filter = ctx.get_source_filter()
                if source_filter:
                    queryset = queryset.filter(__raw__=source_filter)

            # Search with case-insensitive contains
            filter_kwargs = {f"{search_field}__icontains": search_value}
            queryset = queryset.filter(**filter_kwargs)

            # Order by modified date and limit
            queryset = queryset.order_by("-modified").limit(limit)

            results = []
            for obj in queryset:
                display = getattr(obj, display_field, str(obj.id))
                results.append(
                    TLOSearchResult(
                        id=str(obj.id),
                        display_value=str(display) if display else str(obj.id),
                        tlo_type=tlo_type,
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Error searching {tlo_type}: {e}")
            return []
