"""Tests for service management GraphQL operations.

Covers: toggle enabled/triage, query persistence, registration resilience,
and the fix for settings not being reset on container restart.
"""

import sys
import types
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any, cast

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


class TestServiceMetadataReads:
    """Test modern service metadata reads against raw Mongo service docs."""

    def test_services_query_handles_schema_less_legacy_record(
        self, admin_context: GraphQLContext
    ) -> None:
        from django.conf import settings as django_settings

        col = django_settings.PY_DB[django_settings.COL_SERVICES]
        name = "TestApiSchemaLessLegacyService"
        col.delete_many({"name": name})

        try:
            col.insert_one(
                {
                    "name": name,
                    "description": "Legacy service stored without schema_version",
                    "version": "0.9.0",
                    "enabled": True,
                    "run_on_triage": True,
                    "status": "available",
                    "supported_types": ["Sample"],
                    "config": {"api_key": "shh", "timeout": 15},
                }
            )

            result = execute_gql(
                admin_context,
                """
                query {
                    services {
                        name
                        version
                        description
                        enabled
                        runOnTriage
                        supportedTypes
                        isModern
                        configOptions {
                            key
                            value
                        }
                    }
                }
                """,
            )
            assert result.errors is None

            service = next(svc for svc in result.data["services"] if svc["name"] == name)
            assert service["version"] == "0.9.0"
            assert service["description"] == "Legacy service stored without schema_version"
            assert service["enabled"] is True
            assert service["runOnTriage"] is True
            assert service["supportedTypes"] == ["Sample"]
            assert service["isModern"] is False
            assert {opt["key"]: opt["value"] for opt in service["configOptions"]} == {
                "api_key": "shh",
                "timeout": "15",
            }
        finally:
            col.delete_many({"name": name})

    def test_registry_uses_raw_service_records_for_triage(self) -> None:
        from django.conf import settings as django_settings

        from crits_api.worker.services import registry
        from crits_api.worker.services.base import AnalysisContext, AnalysisService, ServiceConfig

        col = django_settings.PY_DB[django_settings.COL_SERVICES]
        modern_name = "TestApiModernRegistryService"
        legacy_name = "TestApiLegacyRegistryService"
        col.delete_many({"name": {"$in": [modern_name, legacy_name]}})

        original_registry = dict(registry._registry)

        class ModernRegistryService(AnalysisService):
            name = modern_name
            version = "1.0.0"
            description = "modern"
            supported_types = ["Sample"]
            run_on_triage = True

            def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
                return None

        try:
            registry._registry.clear()
            registry._registry[modern_name] = ModernRegistryService

            col.insert_many(
                [
                    {
                        "name": modern_name,
                        "enabled": False,
                        "run_on_triage": True,
                        "status": "available",
                    },
                    {
                        "name": legacy_name,
                        "enabled": True,
                        "run_on_triage": True,
                        "status": "available",
                    },
                ]
            )

            assert registry.get_triage_services() == []
            assert registry.get_triage_service_names() == [legacy_name]
        finally:
            registry._registry.clear()
            registry._registry.update(original_registry)
            col.delete_many({"name": {"$in": [modern_name, legacy_name]}})

    def test_build_config_reads_schema_less_service_record(self) -> None:
        from django.conf import settings as django_settings

        from crits_api.worker.services.base import ServiceConfig
        from crits_api.worker.services.execution import _build_config

        col = django_settings.PY_DB[django_settings.COL_SERVICES]
        name = "TestApiSchemaLessConfigService"
        col.delete_many({"name": name})

        @dataclass
        class DemoConfig(ServiceConfig):
            token: str = ""
            timeout: int = 30

        try:
            col.insert_one(
                {
                    "name": name,
                    "config": {"token": "db-token", "timeout": 45},
                }
            )

            config = cast(
                DemoConfig,
                _build_config(DemoConfig, {"timeout": 60}, service_name=name),
            )
            assert config.token == "db-token"
            assert config.timeout == 60
        finally:
            col.delete_many({"name": name})


class TestLegacyServiceRuntime:
    """Test the extracted legacy service runtime used by the worker."""

    def test_execute_service_local_does_not_require_handlers(
        self,
        test_user: Any,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import crits.services as services_pkg
        import crits.services.results as service_results
        from crits.services.analysis_result import AnalysisResult
        from crits.services.core import Service
        from crits.services.runtime import execute_service_local
        from crits.services.service import CRITsService

        name = "TestApiLegacyRuntimeService"
        CRITsService.objects(name=name).delete()
        AnalysisResult.objects(service_name=name).delete()

        class FakeLegacyService(Service):
            name: str = ""
            version: str = ""
            description: str = ""
            supported_types: list[str] = []

            def run(self, obj: Any, config: Any) -> None:
                self._add_result("test", "value")

        FakeLegacyService.name = name
        FakeLegacyService.version = "1.0.0"
        FakeLegacyService.description = "legacy runtime test"
        FakeLegacyService.supported_types = ["Sample"]

        class DummyManager:
            @staticmethod
            def get_service_class(service_name: str) -> type[FakeLegacyService] | None:
                if service_name == name:
                    return FakeLegacyService
                return None

        class DummyQuerySet:
            @staticmethod
            def first() -> object:
                return object()

        class DummySample:
            @staticmethod
            def objects(**kwargs: str) -> DummyQuerySet:
                assert kwargs["id"] == "dummy-id"
                return DummyQuerySet()

        class DummyObj:
            id = "dummy-id"
            _meta = {"crits_type": "Sample"}

        original_handlers = sys.modules.get("crits.services.handlers")
        sys.modules["crits.services.handlers"] = types.ModuleType("crits.services.handlers")

        monkeypatch.setattr(services_pkg, "manager", DummyManager())

        def fake_class_from_type(_: str) -> type[DummySample]:
            return DummySample

        monkeypatch.setattr(service_results, "class_from_type", fake_class_from_type)

        try:
            CRITsService(
                name=name,
                description="Service for runtime tests",
                version="1.0.0",
                status="available",
                enabled=True,
                run_on_triage=False,
                supported_types=["Sample"],
            ).save()

            result = execute_service_local(
                name=name,
                type_="Sample",
                id_="dummy-id",
                user=test_user.username,
                obj=DummyObj(),
            )

            assert result["success"] is True
            assert result["analysis_id"]

            ar = AnalysisResult.objects(analysis_id=result["analysis_id"]).first()
            assert ar is not None
            assert ar.status == "completed"
            assert ar.service_name == name
            assert ar.analyst == test_user.username
            assert ar.results == [{"subtype": "test", "result": "value"}]
        finally:
            AnalysisResult.objects(service_name=name).delete()
            CRITsService.objects(name=name).delete()
            if original_handlers is None:
                sys.modules.pop("crits.services.handlers", None)
            else:
                sys.modules["crits.services.handlers"] = original_handlers


class TestAnalysisRecordReads:
    """Test GraphQL analysis-result reads against raw Mongo documents."""

    def test_analysis_results_query_handles_schema_less_record(
        self,
        admin_context: GraphQLContext,
    ) -> None:
        from django.conf import settings as django_settings

        col = django_settings.PY_DB[django_settings.COL_ANALYSIS_RESULTS]
        analysis_id = "test-api-analysis-results-query"
        col.delete_many({"analysis_id": analysis_id})

        try:
            col.insert_one(
                {
                    "analysis_id": analysis_id,
                    "service_name": "TestApiQueryService",
                    "version": "1.2.3",
                    "object_type": "Sample",
                    "object_id": "abc123",
                    "analyst": "test_api_user",
                    "status": "completed",
                    "start_date": "2026-03-26 11:00:00",
                    "finish_date": "2026-03-26 11:00:05",
                    "results": [{"subtype": "hash", "result": "deadbeef"}],
                    "log": [
                        {
                            "message": "done",
                            "level": "info",
                            "datetime": "2026-03-26 11:00:05",
                        }
                    ],
                }
            )

            result = execute_gql(
                admin_context,
                """
                query {
                    analysisResults(objType: "Sample", objId: "abc123") {
                        analysisId
                        serviceName
                        status
                        results
                        log {
                            message
                            level
                            datetime
                        }
                    }
                }
                """,
            )

            assert result.errors is None
            assert result.data["analysisResults"] == [
                {
                    "analysisId": analysis_id,
                    "serviceName": "TestApiQueryService",
                    "status": "completed",
                    "results": [{"subtype": "hash", "result": "deadbeef"}],
                    "log": [
                        {
                            "message": "done",
                            "level": "info",
                            "datetime": "2026-03-26 11:00:05",
                        }
                    ],
                }
            ]
        finally:
            col.delete_many({"analysis_id": analysis_id})

    def test_analysis_status_handles_schema_less_record(
        self,
        admin_context: GraphQLContext,
    ) -> None:
        from django.conf import settings as django_settings

        col = django_settings.PY_DB[django_settings.COL_ANALYSIS_RESULTS]
        analysis_id = "test-api-analysis-status"
        col.delete_many({"analysis_id": analysis_id})

        try:
            col.insert_one(
                {
                    "analysis_id": analysis_id,
                    "service_name": "TestApiStatusService",
                    "object_type": "Sample",
                    "object_id": "abc123",
                    "status": "started",
                    "start_date": "2026-03-26 11:05:00",
                }
            )

            result = execute_gql(
                admin_context,
                """
                mutation {
                    analysisStatus(analysisId: "test-api-analysis-status") {
                        success
                        message
                        analysisId
                    }
                }
                """,
            )

            assert result.errors is None
            assert result.data["analysisStatus"] == {
                "success": False,
                "message": "Status: started",
                "analysisId": analysis_id,
            }
        finally:
            col.delete_many({"analysis_id": analysis_id})


class TestWorkerAnalysisRecordWrites:
    """Test worker analysis-result writes against raw Mongo documents."""

    def test_create_and_update_analysis_record(self) -> None:
        from django.conf import settings as django_settings

        from crits_api.worker.services.results import (
            create_analysis_record,
            update_analysis_record,
        )

        col = django_settings.PY_DB[django_settings.COL_ANALYSIS_RESULTS]
        service_name = "TestApiWorkerWriteService"
        col.delete_many({"service_name": service_name})

        try:
            analysis_id = create_analysis_record(
                service_name=service_name,
                version="1.0.0",
                obj_type="Sample",
                obj_id="abc123",
                username="test_api_user",
                config={"token": "abc"},
            )

            created = col.find_one({"analysis_id": analysis_id})
            assert created is not None
            assert created["schema_version"] == 1
            assert created["status"] == "started"
            assert created["config"] == {"token": "abc"}

            update_analysis_record(
                analysis_id=analysis_id,
                results=[{"subtype": "hash", "result": "deadbeef"}],
                log_entries=[{"message": "done", "level": "info"}],
                status="completed",
            )

            updated = col.find_one({"analysis_id": analysis_id})
            assert updated["status"] == "completed"
            assert updated["finish_date"]
            assert updated["results"] == [{"subtype": "hash", "result": "deadbeef"}]
            assert updated["log"] == [
                {
                    "message": "done",
                    "level": "info",
                    "datetime": updated["log"][0]["datetime"],
                }
            ]
        finally:
            col.delete_many({"service_name": service_name})

    def test_mark_analysis_error(self) -> None:
        from django.conf import settings as django_settings

        from crits_api.worker.services.results import (
            create_analysis_record,
            mark_analysis_error,
        )

        col = django_settings.PY_DB[django_settings.COL_ANALYSIS_RESULTS]
        service_name = "TestApiWorkerErrorService"
        col.delete_many({"service_name": service_name})

        try:
            analysis_id = create_analysis_record(
                service_name=service_name,
                version="1.0.0",
                obj_type="Sample",
                obj_id="abc123",
                username="test_api_user",
            )

            mark_analysis_error(analysis_id, "boom")

            errored = col.find_one({"analysis_id": analysis_id})
            assert errored["status"] == "error"
            assert errored["finish_date"]
            assert errored["log"][-1]["message"] == "boom"
            assert errored["log"][-1]["level"] == "error"
            assert errored["schema_version"] == 1
        finally:
            col.delete_many({"service_name": service_name})


class TestSyncLegacyServices:
    """Test the explicit legacy-service sync mutation."""

    def test_sync_legacy_services(
        self,
        admin_context: GraphQLContext,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import crits.services as services_pkg
        import crits.services.core as services_core

        calls: list[str] = []

        def fake_sync() -> dict[str, int]:
            calls.append("sync")
            return {"created": 1, "updated": 2, "unavailable": 3, "total": 3}

        def fake_reset() -> None:
            calls.append("reset")

        monkeypatch.setattr(services_core, "sync_legacy_service_records", fake_sync)
        monkeypatch.setattr(services_pkg, "reset_service_manager", fake_reset)

        result = execute_gql(
            admin_context,
            """
            mutation {
                syncLegacyServices {
                    success
                    message
                }
            }
            """,
        )

        assert result.errors is None
        assert result.data["syncLegacyServices"]["success"] is True
        assert "1 created" in result.data["syncLegacyServices"]["message"]
        assert "2 updated" in result.data["syncLegacyServices"]["message"]
        assert "3 unavailable" in result.data["syncLegacyServices"]["message"]
        assert calls == ["sync", "reset"]

    def test_sync_legacy_services_unauthenticated(self, anon_context: GraphQLContext) -> None:
        result = execute_gql(
            anon_context,
            """
            mutation {
                syncLegacyServices {
                    success
                }
            }
            """,
        )
        assert result.errors is not None
