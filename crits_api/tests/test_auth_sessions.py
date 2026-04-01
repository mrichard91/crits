"""Tests for GraphQL auth mutations and raw session-backed user loading."""

import asyncio
import sys
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from crits_api.auth.context import GraphQLContext
from crits_api.auth.redis_session import create_session
from crits_api.auth.session import get_session_data, get_user_from_session
from crits_api.config import settings
from crits_api.db.auth_records import AuthConfig
from crits_api.tests.conftest import TEST_PASS, TEST_USER, execute_gql


def _request_with_headers() -> MagicMock:
    request = MagicMock()
    request.cookies = {}
    request.headers = {"user-agent": "pytest", "accept-language": "en-US"}
    request.client = MagicMock(host="127.0.0.1")
    return request


def test_login_creates_session_and_session_lookup() -> None:
    response = MagicMock()
    context = GraphQLContext(request=_request_with_headers(), response=response, user=None)

    result = execute_gql(
        context,
        f"""
        mutation {{
            login(username: "{TEST_USER}", password: "{TEST_PASS}") {{
                success message status
            }}
        }}
        """,
    )
    assert result.errors is None
    assert result.data["login"]["success"] is True
    assert result.data["login"]["status"] == "login_successful"

    call = response.set_cookie.call_args
    assert call is not None
    session_key = call.kwargs["value"]

    request = MagicMock()
    request.cookies = {settings.session_cookie_name: session_key}

    user = asyncio.run(get_user_from_session(request))
    assert user is not None
    assert user.username == TEST_USER
    assert user.is_superuser is True


def test_login_rejects_bad_password() -> None:
    response = MagicMock()
    context = GraphQLContext(request=_request_with_headers(), response=response, user=None)

    result = execute_gql(
        context,
        f"""
        mutation {{
            login(username: "{TEST_USER}", password: "wrong-password") {{
                success message status
            }}
        }}
        """,
    )
    assert result.errors is None
    assert result.data["login"]["success"] is False
    assert result.data["login"]["status"] == "login_failed"


def test_logout_deletes_session(test_user: Any) -> None:
    session_key = create_session(settings.redis_url, str(test_user.id), 60)
    request = _request_with_headers()
    request.cookies = {settings.session_cookie_name: session_key}
    response = MagicMock()
    context = GraphQLContext(request=request, response=response, user=None)

    result = execute_gql(
        context,
        """
        mutation {
            logout {
                success message
            }
        }
        """,
    )
    assert result.errors is None
    assert result.data["logout"]["success"] is True
    response.delete_cookie.assert_called_once_with("sessionid", path="/")
    assert asyncio.run(get_session_data(session_key)) is None


def test_get_user_from_session_without_cookie() -> None:
    request = MagicMock()
    request.cookies = {}
    assert asyncio.run(get_user_from_session(request)) is None


def test_login_ldap_secret_generation_uses_raw_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = MagicMock()
    context = GraphQLContext(request=_request_with_headers(), response=response, user=None)

    from crits_api.graphql.mutations import auth as auth_mutation

    user = SimpleNamespace(
        id="507f1f77bcf86cd799439011",
        username=TEST_USER,
        secret="",
        totp=False,
        is_active=True,
        invalid_login_attempts=0,
        get_access_list=lambda update=False: {},
    )
    updated: list[tuple[str, dict[str, object]]] = []

    fake_core_user: Any = ModuleType("crits.core.user")

    class FakeAuthBackend:
        def authenticate(self, **kwargs: object) -> object:
            return user

    fake_core_user.CRITsAuthBackend = FakeAuthBackend

    def fake_update_auth_user_by_username(
        username: str,
        *,
        set_fields: dict[str, object],
    ) -> object:
        updated.append((username, set_fields))
        return object()

    monkeypatch.setitem(sys.modules, "crits.core.user", fake_core_user)
    monkeypatch.setattr(
        auth_mutation, "get_auth_config", lambda: AuthConfig(ldap_auth=True, totp_web="Required")
    )
    monkeypatch.setattr(
        auth_mutation,
        "gen_user_secret",
        lambda totp_pass, username: ("encrypted-secret", "plain-secret"),
    )
    monkeypatch.setattr(
        auth_mutation, "update_auth_user_by_username", fake_update_auth_user_by_username
    )

    result = execute_gql(
        context,
        f"""
        mutation {{
            login(username: "{TEST_USER}", password: "{TEST_PASS}", totpPass: "123456") {{
                success message status totpSecret
            }}
        }}
        """,
    )

    assert result.errors is None
    assert result.data["login"]["success"] is False
    assert result.data["login"]["status"] == "secret_generated"
    assert result.data["login"]["totpSecret"] == "plain-secret"
    assert updated == [
        (
            TEST_USER,
            {"secret": "encrypted-secret", "totp": True},
        )
    ]
