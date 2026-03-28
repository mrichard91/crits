"""Regression tests for lazy legacy service-manager initialization."""

import importlib

from pytest import MonkeyPatch


def test_service_manager_is_lazy_and_cached(monkeypatch: MonkeyPatch) -> None:
    """Importing crits.services should not register services until first use."""
    import crits.services as services
    import crits.services.core as services_core

    calls: list[str] = []

    class FakeServiceManager:
        def __init__(self) -> None:
            calls.append("built")

        def get_service_class(self, service_name: str) -> dict[str, str]:
            return {"name": service_name}

    monkeypatch.setattr(services_core, "ServiceManager", FakeServiceManager)
    importlib.reload(services)

    try:
        assert calls == []
        assert services.manager.get_service_class("ssdeep") == {"name": "ssdeep"}
        assert calls == ["built"]

        assert services.manager.get_service_class("yara_scan") == {"name": "yara_scan"}
        assert calls == ["built"]
    finally:
        services.reset_service_manager()
        importlib.reload(services)


def test_service_record_sync_is_explicit() -> None:
    """Constructing a manager should not write DB records until sync is requested."""
    from crits.services.core import Service, ServiceManager
    from crits.services.service_records import (
        delete_service_records,
        get_service_record,
    )

    service_name = "TestApiExplicitSyncService"
    delete_service_records({"name": service_name})

    class ExplicitSyncService(Service):
        name = service_name
        version = "1.2.3"
        description = "Service used to verify explicit sync behavior"
        supported_types = ["Sample"]

        @staticmethod
        def get_config(existing_config: dict[str, str]) -> dict[str, str]:
            config = dict(existing_config)
            config.setdefault("token", "abc123")
            return config

    try:
        manager = ServiceManager(services_packages=[])
        assert get_service_record(service_name) is None

        manager._services = {service_name: ExplicitSyncService}
        summary = manager.sync_service_records(mark_unavailable=False)

        svc = get_service_record(service_name)
        assert svc is not None
        assert svc.status == "available"
        assert svc.version == "1.2.3"
        assert svc.description == "Service used to verify explicit sync behavior"
        assert list(svc.supported_types) == ["Sample"]
        assert svc.config["token"] == "abc123"
        assert summary["created"] == 1
        assert summary["updated"] == 0
        assert summary["unavailable"] == 0
    finally:
        delete_service_records({"name": service_name})
