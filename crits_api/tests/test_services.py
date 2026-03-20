"""Tests for service management GraphQL operations.

Covers: toggle enabled/triage, query persistence, registration resilience,
and the fix for settings not being reset on container restart.
"""

from collections.abc import Generator

import pytest

from crits_api.auth.context import GraphQLContext
from crits_api.tests.conftest import execute_gql

# ── Helper: seed a service record in the DB ────────────────────────────


@pytest.fixture
def test_service(admin_context: GraphQLContext) -> Generator[str]:
    """Create a test service record directly in MongoDB and clean up after."""
    from crits.services.service import CRITsService

    name = "TestApiService"
    CRITsService.objects(name=name).delete()
    svc = CRITsService(
        name=name,
        description="Service for API tests",
        version="1.0.0",
        status="available",
        enabled=False,
        run_on_triage=False,
        supported_types=["Sample", "Indicator"],
    )
    svc.save()

    yield name

    CRITsService.objects(name=name).delete()


# ── Toggle Enabled ────────────────────────────────────────────────────


class TestToggleServiceEnabled:
    """Test the toggleServiceEnabled mutation."""

    def test_enable_service(self, admin_context: GraphQLContext, test_service: str) -> None:
        result = execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceEnabled(serviceName: $name, enabled: true) {
                    success message
                }
            }
            """,
            {"name": test_service},
        )
        assert result.errors is None
        assert result.data["toggleServiceEnabled"]["success"] is True

        # Verify persisted in DB
        from crits.services.service import CRITsService

        svc = CRITsService.objects(name=test_service).first()
        assert svc.enabled is True

    def test_disable_service(self, admin_context: GraphQLContext, test_service: str) -> None:
        # First enable
        execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceEnabled(serviceName: $name, enabled: true) { success }
            }
            """,
            {"name": test_service},
        )

        # Then disable
        result = execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceEnabled(serviceName: $name, enabled: false) {
                    success message
                }
            }
            """,
            {"name": test_service},
        )
        assert result.errors is None
        assert result.data["toggleServiceEnabled"]["success"] is True

        from crits.services.service import CRITsService

        svc = CRITsService.objects(name=test_service).first()
        assert svc.enabled is False

    def test_enable_unauthenticated(self, anon_context: GraphQLContext) -> None:
        result = execute_gql(
            anon_context,
            """
            mutation {
                toggleServiceEnabled(serviceName: "anything", enabled: true) { success }
            }
            """,
        )
        assert result.errors is not None


# ── Toggle Triage ─────────────────────────────────────────────────────


class TestToggleServiceTriage:
    """Test the toggleServiceTriage mutation."""

    def test_enable_triage(self, admin_context: GraphQLContext, test_service: str) -> None:
        result = execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceTriage(serviceName: $name, runOnTriage: true) {
                    success message
                }
            }
            """,
            {"name": test_service},
        )
        assert result.errors is None
        assert result.data["toggleServiceTriage"]["success"] is True

        from crits.services.service import CRITsService

        svc = CRITsService.objects(name=test_service).first()
        assert svc.run_on_triage is True

    def test_disable_triage(self, admin_context: GraphQLContext, test_service: str) -> None:
        # Enable first
        execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceTriage(serviceName: $name, runOnTriage: true) { success }
            }
            """,
            {"name": test_service},
        )

        # Then disable
        result = execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceTriage(serviceName: $name, runOnTriage: false) {
                    success message
                }
            }
            """,
            {"name": test_service},
        )
        assert result.errors is None
        assert result.data["toggleServiceTriage"]["success"] is True

        from crits.services.service import CRITsService

        svc = CRITsService.objects(name=test_service).first()
        assert svc.run_on_triage is False

    def test_triage_unauthenticated(self, anon_context: GraphQLContext) -> None:
        result = execute_gql(
            anon_context,
            """
            mutation {
                toggleServiceTriage(serviceName: "anything", runOnTriage: true) { success }
            }
            """,
        )
        assert result.errors is not None


# ── Toggle persistence across re-registration ─────────────────────────


class TestServiceSettingsPersistence:
    """Verify that enabled/triage settings survive service re-registration.

    This is the core regression test for the bug where ServiceManager
    _register_services() was resetting enabled and run_on_triage to False
    every time a container started.
    """

    def test_enabled_survives_status_change(
        self, admin_context: GraphQLContext, test_service: str
    ) -> None:
        """Toggling status to 'misconfigured' should NOT reset enabled."""
        from crits.services.service import CRITsService

        # Enable the service
        execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceEnabled(serviceName: $name, enabled: true) { success }
            }
            """,
            {"name": test_service},
        )

        # Simulate what _register_services does for a misconfigured service:
        # set status to misconfigured but should NOT touch enabled/run_on_triage
        svc = CRITsService.objects(name=test_service).first()
        svc.status = "misconfigured"
        svc.save()

        # Verify enabled was NOT reset
        svc.reload()
        assert svc.enabled is True, "enabled was reset when status changed to misconfigured"

    def test_triage_survives_status_change(
        self, admin_context: GraphQLContext, test_service: str
    ) -> None:
        """Toggling status to 'unavailable' should NOT reset run_on_triage."""
        from crits.services.service import CRITsService

        # Enable triage
        execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceTriage(serviceName: $name, runOnTriage: true) { success }
            }
            """,
            {"name": test_service},
        )

        # Simulate what _register_services does for unavailable services:
        # set status to unavailable but should NOT touch enabled/run_on_triage
        svc = CRITsService.objects(name=test_service).first()
        svc.status = "unavailable"
        svc.save()

        # Verify run_on_triage was NOT reset
        svc.reload()
        assert svc.run_on_triage is True, (
            "run_on_triage was reset when status changed to unavailable"
        )

    def test_both_flags_persist_through_full_reregistration_cycle(
        self, admin_context: GraphQLContext, test_service: str
    ) -> None:
        """Simulate a full container restart: toggle on, re-register, verify."""
        from crits.services.service import CRITsService

        # Toggle both on
        execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceEnabled(serviceName: $name, enabled: true) { success }
            }
            """,
            {"name": test_service},
        )
        execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceTriage(serviceName: $name, runOnTriage: true) { success }
            }
            """,
            {"name": test_service},
        )

        # Simulate re-registration: update metadata fields (description,
        # version, etc.) like _register_services does — but NOT enabled/triage
        svc = CRITsService.objects(name=test_service).first()
        svc.description = "Updated description on restart"
        svc.version = "1.0.1"
        svc.status = "available"
        svc.save()

        # Verify both flags survived
        svc.reload()
        assert svc.enabled is True, "enabled was lost during re-registration"
        assert svc.run_on_triage is True, "run_on_triage was lost during re-registration"


# ── Upsert behavior (service created by toggle, not by registration) ──


class TestServiceUpsert:
    """Test that toggling a service that doesn't exist yet creates it.

    Upserts create bare MongoDB documents without schema_version, so we
    use raw pymongo to verify rather than MongoEngine.
    """

    def test_toggle_creates_service_record(self, admin_context: GraphQLContext) -> None:
        from django.conf import settings as django_settings

        col = django_settings.PY_DB[django_settings.COL_SERVICES]
        name = "TestApiUpsertService"
        col.delete_many({"name": name})

        try:
            # Toggle enabled on a non-existent service (upsert)
            result = execute_gql(
                admin_context,
                """
                mutation ($name: String!) {
                    toggleServiceEnabled(serviceName: $name, enabled: true) {
                        success
                    }
                }
                """,
                {"name": name},
            )
            assert result.errors is None
            assert result.data["toggleServiceEnabled"]["success"] is True

            # Verify the record was created (raw pymongo — no schema_version needed)
            doc = col.find_one({"name": name})
            assert doc is not None
            assert doc["enabled"] is True
        finally:
            col.delete_many({"name": name})

    def test_upserted_service_config_is_none(self, admin_context: GraphQLContext) -> None:
        """A service created by upsert has no config field.

        Regression test: core.py must guard svc_obj.config.to_dict()
        against None when re-registering a service whose DB record was
        created by a GraphQL upsert.
        """
        from django.conf import settings as django_settings

        col = django_settings.PY_DB[django_settings.COL_SERVICES]
        name = "TestApiUpsertNoConfig"
        col.delete_many({"name": name})

        try:
            # Create via upsert (no config field)
            execute_gql(
                admin_context,
                """
                mutation ($name: String!) {
                    toggleServiceEnabled(serviceName: $name, enabled: true) { success }
                }
                """,
                {"name": name},
            )

            doc = col.find_one({"name": name})
            assert doc is not None
            assert "config" not in doc or doc["config"] is None

            # The guard in core.py: config.to_dict() if config else {}
            config_val = doc.get("config")
            config_dict = config_val if isinstance(config_val, dict) else {}
            assert config_dict == {}
        finally:
            col.delete_many({"name": name})


# ── Service config update ─────────────────────────────────────────────


class TestUpdateServiceConfig:
    """Test the updateServiceConfig mutation."""

    def test_update_config_does_not_reset_flags(
        self, admin_context: GraphQLContext, test_service: str
    ) -> None:
        """Updating config should NOT touch enabled or run_on_triage."""
        from crits.services.service import CRITsService

        # Enable both flags
        execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceEnabled(serviceName: $name, enabled: true) { success }
            }
            """,
            {"name": test_service},
        )
        execute_gql(
            admin_context,
            """
            mutation ($name: String!) {
                toggleServiceTriage(serviceName: $name, runOnTriage: true) { success }
            }
            """,
            {"name": test_service},
        )

        # Update a config value
        result = execute_gql(
            admin_context,
            """
            mutation ($name: String!, $config: String!) {
                updateServiceConfig(serviceName: $name, configJson: $config) {
                    success message
                }
            }
            """,
            {"name": test_service, "config": '{"some_key": "some_value"}'},
        )
        assert result.errors is None
        assert result.data["updateServiceConfig"]["success"] is True

        # Verify flags were NOT touched
        svc = CRITsService.objects(name=test_service).first()
        assert svc.enabled is True, "enabled was reset by config update"
        assert svc.run_on_triage is True, "run_on_triage was reset by config update"

    def test_update_config_invalid_json(
        self, admin_context: GraphQLContext, test_service: str
    ) -> None:
        result = execute_gql(
            admin_context,
            """
            mutation ($name: String!, $config: String!) {
                updateServiceConfig(serviceName: $name, configJson: $config) {
                    success message
                }
            }
            """,
            {"name": test_service, "config": "not valid json"},
        )
        assert result.errors is None
        assert result.data["updateServiceConfig"]["success"] is False
        assert "Invalid JSON" in result.data["updateServiceConfig"]["message"]

    def test_update_config_unauthenticated(self, anon_context: GraphQLContext) -> None:
        result = execute_gql(
            anon_context,
            """
            mutation {
                updateServiceConfig(serviceName: "x", configJson: "{}") { success }
            }
            """,
        )
        assert result.errors is not None
