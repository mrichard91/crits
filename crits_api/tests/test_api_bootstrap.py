"""Tests for lazy API-side Django bootstrap behavior."""

import asyncio
import builtins
import importlib
from unittest.mock import MagicMock

import pytest

from crits_api.db import connection


def _request_with_query(query: str, *, content_type: str = "application/json") -> MagicMock:
    """Build a minimal request mock for GraphQL context tests."""

    request = MagicMock()
    request.method = "POST"
    request.headers = {"content-type": content_type}

    async def fake_json() -> dict[str, str]:
        return {"query": query}

    request.json = fake_json
    return request


def test_api_lifespan_does_not_connect_django(monkeypatch: pytest.MonkeyPatch) -> None:
    """FastAPI startup should not eagerly bootstrap the legacy Django layer."""

    monkeypatch.setattr(connection, "_django_setup", False)

    import crits_api.main as main

    importlib.reload(main)

    async def run_lifespan() -> None:
        async with main.lifespan(main.app):
            assert connection.is_connected() is False

    asyncio.run(run_lifespan())
    assert connection.is_connected() is False


def test_graphql_context_bootstraps_legacy_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    """GraphQL requests should bootstrap Django lazily when context is created."""

    from crits_api.graphql import context as graphql_context

    calls: list[str] = []

    async def fake_get_user_from_session(_request: object) -> None:
        return None

    monkeypatch.setattr(graphql_context, "ensure_connected", lambda: calls.append("connect"))
    monkeypatch.setattr(graphql_context, "get_user_from_session", fake_get_user_from_session)

    request = _request_with_query("query { actors(limit: 1) { totalCount } }")
    ctx = asyncio.run(graphql_context.get_context(request, MagicMock()))

    assert calls == ["connect"]
    assert ctx.user is None


def test_graphql_auth_context_skips_legacy_connection_when_ldap_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auth-only GraphQL requests should stay off Django when LDAP auth is disabled."""

    from crits_api.graphql import context as graphql_context

    calls: list[str] = []

    async def fake_get_user_from_session(_request: object) -> None:
        return None

    monkeypatch.setattr(graphql_context, "ensure_connected", lambda: calls.append("connect"))
    monkeypatch.setattr(graphql_context, "get_user_from_session", fake_get_user_from_session)

    request = _request_with_query('mutation { login(username: "u", password: "p") { success } }')
    ctx = asyncio.run(graphql_context.get_context(request, MagicMock()))

    assert calls == []
    assert ctx.user is None


def test_graphql_auth_context_skips_legacy_connection_with_ldap_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auth-only GraphQL requests should stay off Django even when LDAP is enabled."""

    from crits_api.graphql import context as graphql_context

    calls: list[str] = []

    async def fake_get_user_from_session(_request: object) -> None:
        return None

    monkeypatch.setattr(graphql_context, "ensure_connected", lambda: calls.append("connect"))
    monkeypatch.setattr(graphql_context, "get_user_from_session", fake_get_user_from_session)

    request = _request_with_query('mutation { login(username: "u", password: "p") { success } }')
    ctx = asyncio.run(graphql_context.get_context(request, MagicMock()))

    assert calls == []
    assert ctx.user is None


def test_download_unauthenticated_does_not_import_sample(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Anonymous download requests should fail before importing legacy models."""

    from crits_api.routes import download

    imported_sample: list[str] = []
    original_import = builtins.__import__

    async def fake_get_user_from_session(_request: object) -> None:
        return None

    def guarded_import(
        name: str,
        globals_: dict | None = None,
        locals_: dict | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "crits.samples.sample":
            imported_sample.append(name)
            raise AssertionError("download route imported Sample before authentication")
        return original_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(download, "get_user_from_session", fake_get_user_from_session)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    response = asyncio.run(download.download_sample(MagicMock(), "a" * 32))

    assert response.status_code == 401
    assert imported_sample == []
