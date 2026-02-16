"""Bulk operation mutation resolvers."""

import logging

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.permissions import require_authenticated
from crits_api.cache.decorators import _fire_invalidation
from crits_api.graphql.types.common import BulkResult

logger = logging.getLogger(__name__)

# Cache key prefix for each TLO type
_TYPE_CACHE_KEY = {
    "Indicator": "indicator",
    "Actor": "actor",
    "Backdoor": "backdoor",
    "Campaign": "campaign",
    "Certificate": "certificate",
    "Domain": "domain",
    "Email": "email",
    "Event": "event",
    "Exploit": "exploit",
    "IP": "ip",
    "PCAP": "pcap",
    "RawData": "raw_data",
    "Sample": "sample",
    "Screenshot": "screenshot",
    "Signature": "signature",
    "Target": "target",
}


def _invalidate_tlo_type(tlo_type: str) -> None:
    from crits_api.config import settings

    if settings.cache_enabled and tlo_type in _TYPE_CACHE_KEY:
        _fire_invalidation((_TYPE_CACHE_KEY[tlo_type],))


# Mapping of TLO type names to their delete handlers
TLO_DELETE_HANDLERS = {
    "Sample": ("crits.samples.handlers", "delete_sample", "md5"),
    "Indicator": ("crits.indicators.handlers", "indicator_remove", "id"),
    "Domain": ("crits.domains.domain", "Domain", "delete"),
    "Actor": ("crits.actors.handlers", "actor_remove", "id"),
    "Campaign": ("crits.campaigns.handlers", "remove_campaign", "name"),
    "Event": ("crits.events.handlers", "event_remove", "id"),
    "IP": ("crits.ips.ip", "IP", "delete"),
    "Backdoor": ("crits.backdoors.handlers", "backdoor_remove", "id"),
    "Exploit": ("crits.exploits.handlers", "exploit_remove", "id"),
    "Email": ("crits.emails.email", "Email", "delete"),
    "PCAP": ("crits.pcaps.handlers", "delete_pcap", "md5"),
    "Certificate": ("crits.certificates.handlers", "delete_cert", "md5"),
    "RawData": ("crits.raw_data.handlers", "delete_raw_data", "id"),
    "Signature": ("crits.signatures.handlers", "delete_signature", "id"),
    "Target": ("crits.targets.handlers", "remove_target", "email"),
    "Screenshot": ("crits.screenshots.screenshot", "Screenshot", "delete"),
}


@strawberry.type
class BulkMutations:
    @strawberry.mutation(description="Bulk update status for multiple TLOs")
    @require_authenticated
    def bulk_update_status(
        self,
        info: Info,
        tlo_type: str,
        ids: list[str],
        status: str,
    ) -> BulkResult:
        """
        Update the status of multiple TLOs at once.

        Args:
            tlo_type: The TLO type (e.g., "Sample", "Indicator")
            ids: List of ObjectIds to update
            status: New status value (e.g., "In Progress", "Analyzed")

        Returns:
            BulkResult with counts of succeeded and failed operations
        """
        from crits.core.handlers import status_update

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        succeeded = 0
        failed = 0
        errors: list[str] = []

        for obj_id in ids:
            try:
                result = status_update(tlo_type, obj_id, status, username)
                if result.get("success"):
                    succeeded += 1
                else:
                    failed += 1
                    errors.append(f"{obj_id}: {result.get('message', 'Unknown error')}")
            except Exception as e:
                failed += 1
                errors.append(f"{obj_id}: {e!s}")

        if succeeded > 0:
            _invalidate_tlo_type(tlo_type)

        return BulkResult(
            success=failed == 0,
            total=len(ids),
            succeeded=succeeded,
            failed=failed,
            errors=errors[:10],  # Limit errors to first 10
        )

    @strawberry.mutation(description="Bulk add TLOs to a campaign")
    @require_authenticated
    def bulk_add_to_campaign(
        self,
        info: Info,
        tlo_type: str,
        ids: list[str],
        campaign: str,
        confidence: str = "low",
    ) -> BulkResult:
        """
        Add multiple TLOs to a campaign.

        Args:
            tlo_type: The TLO type (e.g., "Sample", "Indicator")
            ids: List of ObjectIds to add to campaign
            campaign: Campaign name to add the TLOs to
            confidence: Confidence level (low, medium, high)

        Returns:
            BulkResult with counts of succeeded and failed operations
        """
        from crits.core.class_mapper import class_from_id

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        succeeded = 0
        failed = 0
        errors: list[str] = []

        for obj_id in ids:
            try:
                obj = class_from_id(tlo_type, obj_id)
                if not obj:
                    failed += 1
                    errors.append(f"{obj_id}: Object not found")
                    continue

                # Use the add_campaign method on the object
                obj.add_campaign(
                    campaign_item={
                        "name": campaign,
                        "confidence": confidence,
                        "analyst": username,
                    }
                )
                obj.save(username=username)
                succeeded += 1
            except Exception as e:
                failed += 1
                errors.append(f"{obj_id}: {e!s}")

        if succeeded > 0:
            _invalidate_tlo_type(tlo_type)

        return BulkResult(
            success=failed == 0,
            total=len(ids),
            succeeded=succeeded,
            failed=failed,
            errors=errors[:10],
        )

    @strawberry.mutation(description="Bulk delete multiple TLOs")
    @require_authenticated
    def bulk_delete(
        self,
        info: Info,
        tlo_type: str,
        ids: list[str],
    ) -> BulkResult:
        """
        Delete multiple TLOs at once.

        Args:
            tlo_type: The TLO type (e.g., "Sample", "Indicator")
            ids: List of ObjectIds to delete

        Returns:
            BulkResult with counts of succeeded and failed operations
        """
        from importlib import import_module

        from crits.core.class_mapper import class_from_id

        ctx: GraphQLContext = info.context
        username = ctx.user.username if ctx.user else "unknown"

        succeeded = 0
        failed = 0
        errors: list[str] = []

        handler_info = TLO_DELETE_HANDLERS.get(tlo_type)
        if not handler_info:
            return BulkResult(
                success=False,
                total=len(ids),
                succeeded=0,
                failed=len(ids),
                errors=[f"Unknown TLO type: {tlo_type}"],
            )

        module_path, func_or_class, param_type = handler_info

        for obj_id in ids:
            try:
                # Get the object first to retrieve needed identifiers
                obj = class_from_id(tlo_type, obj_id)
                if not obj:
                    failed += 1
                    errors.append(f"{obj_id}: Object not found")
                    continue

                # Handle different delete patterns
                if param_type == "delete":
                    # Direct model delete
                    obj.delete(username=username)
                    succeeded += 1
                elif param_type == "md5":
                    # Handler that takes MD5
                    module = import_module(module_path)
                    handler = getattr(module, func_or_class)
                    result = handler(obj.md5, username)
                    if result:
                        succeeded += 1
                    else:
                        failed += 1
                        errors.append(f"{obj_id}: Delete failed")
                elif param_type == "id":
                    # Handler that takes ID
                    module = import_module(module_path)
                    handler = getattr(module, func_or_class)
                    result = handler(obj_id, username)
                    if isinstance(result, dict):
                        if result.get("success"):
                            succeeded += 1
                        else:
                            failed += 1
                            errors.append(f"{obj_id}: {result.get('message', 'Delete failed')}")
                    elif result:
                        succeeded += 1
                    else:
                        failed += 1
                        errors.append(f"{obj_id}: Delete failed")
                elif param_type == "name":
                    # Campaign uses name
                    module = import_module(module_path)
                    handler = getattr(module, func_or_class)
                    result = handler(obj.name, username)
                    if result.get("success"):
                        succeeded += 1
                    else:
                        failed += 1
                        errors.append(f"{obj_id}: {result.get('message', 'Delete failed')}")
                elif param_type == "email":
                    # Target uses email_address
                    module = import_module(module_path)
                    handler = getattr(module, func_or_class)
                    result = handler(email_address=obj.email_address, analyst=username)
                    if result.get("success"):
                        succeeded += 1
                    else:
                        failed += 1
                        errors.append(f"{obj_id}: {result.get('message', 'Delete failed')}")
                else:
                    failed += 1
                    errors.append(f"{obj_id}: Unknown delete pattern")

            except Exception as e:
                failed += 1
                errors.append(f"{obj_id}: {e!s}")

        if succeeded > 0:
            _invalidate_tlo_type(tlo_type)

        return BulkResult(
            success=failed == 0,
            total=len(ids),
            succeeded=succeeded,
            failed=failed,
            errors=errors[:10],
        )
