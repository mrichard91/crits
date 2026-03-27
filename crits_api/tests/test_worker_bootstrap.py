"""Tests for lazy worker bootstrap behavior."""

import importlib
import sys

import pytest

from crits_api.db import connection


def test_worker_app_import_does_not_connect_django(monkeypatch: pytest.MonkeyPatch) -> None:
    """Importing the worker app should not eagerly bootstrap Django."""

    monkeypatch.setattr(connection, "_django_setup", False)
    sys.modules.pop("crits_api.worker.app", None)

    importlib.import_module("crits_api.worker.app")

    assert connection.is_connected() is False


def test_worker_task_before_start_connects_when_disconnected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Worker tasks should bootstrap Django only when execution starts."""

    from crits_api.worker.tasks.base import CRITsTask

    calls: list[str] = []

    monkeypatch.setattr("crits_api.worker.tasks.base.is_connected", lambda: False)
    monkeypatch.setattr(
        "crits_api.db.connection.connect_mongodb",
        lambda: calls.append("connect"),
    )

    task = CRITsTask()
    task.before_start("test-task-id", (), {})

    assert calls == ["connect"]


def test_worker_task_before_start_skips_connect_when_connected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Worker tasks should not reconnect if Django is already initialized."""

    from crits_api.worker.tasks.base import CRITsTask

    calls: list[str] = []

    monkeypatch.setattr("crits_api.worker.tasks.base.is_connected", lambda: True)
    monkeypatch.setattr(
        "crits_api.db.connection.connect_mongodb",
        lambda: calls.append("connect"),
    )

    task = CRITsTask()
    task.before_start("test-task-id", (), {})

    assert calls == []
