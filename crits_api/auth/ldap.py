"""LDAP authentication helpers for the modern API auth flow."""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Any

from crits_api.db.auth_records import AuthConfig

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LdapProfile:
    """Normalized LDAP profile fields."""

    first_name: str = ""
    last_name: str = ""
    email: str = ""

    def as_update_fields(self) -> dict[str, str]:
        """Return Mongo `$set` fields for a user profile update."""

        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
        }


@dataclass(slots=True)
class LdapAuthResult:
    """Outcome of an LDAP authentication attempt."""

    authenticated: bool
    profile: LdapProfile | None = None


def _load_ldap_module() -> Any | None:
    """Import python-ldap lazily so the common path stays dependency-light."""

    try:
        return importlib.import_module("ldap")
    except Exception:
        logger.warning("python-ldap is not available; LDAP authentication disabled")
        return None


def _escape_filter_value(ldap: Any, value: str) -> str:
    """Escape LDAP filter values when the helper exists, else fall back to the raw string."""

    filter_module = getattr(ldap, "filter", None)
    escape = getattr(filter_module, "escape_filter_chars", None)
    if callable(escape):
        return str(escape(value))
    return value


def _ldap_url(config: AuthConfig) -> str:
    host, separator, port = config.ldap_server.partition(":")
    scheme = "ldaps" if config.ldap_tls else "ldap"
    if separator and port:
        return f"{scheme}://{host}:{port}"
    return f"{scheme}://{host}"


def _initialize_client(ldap: Any, config: AuthConfig) -> Any:
    client = ldap.initialize(_ldap_url(config))
    client.protocol_version = 3
    client.set_option(ldap.OPT_REFERRALS, 0)
    client.set_option(ldap.OPT_TIMEOUT, 10)
    return client


def _unbind(client: Any) -> None:
    try:
        unbind = getattr(client, "unbind_s", None) or getattr(client, "unbind", None)
        if callable(unbind):
            unbind()
    except Exception:
        logger.debug("Failed to unbind LDAP client cleanly", exc_info=True)


def _search_user_dn(client: Any, ldap: Any, username: str, config: AuthConfig) -> str | None:
    escaped_username = _escape_filter_value(ldap, username)
    search_filter = f"(|(cn={escaped_username})(uid={escaped_username})(mail={escaped_username}))"
    results = client.search_s(config.ldap_userdn, ldap.SCOPE_SUBTREE, search_filter, ["dn"])
    if not results:
        return None

    user_dn = results[0][0]
    return str(user_dn) if user_dn else None


def _build_bind_username(
    client: Any,
    ldap: Any,
    username: str,
    config: AuthConfig,
) -> str | None:
    if config.ldap_bind_dn:
        client.simple_bind_s(config.ldap_bind_dn, config.ldap_bind_password)
        return _search_user_dn(client, ldap, username, config)

    if config.ldap_usercn:
        return f"{config.ldap_usercn}{username},{config.ldap_userdn}"
    if "@" in config.ldap_userdn:
        return f"{username}{config.ldap_userdn}"
    return username


def _search_profile(
    client: Any, ldap: Any, username: str, config: AuthConfig
) -> LdapProfile | None:
    escaped_username = _escape_filter_value(ldap, username)
    results = client.search_s(
        config.ldap_userdn,
        ldap.SCOPE_SUBTREE,
        f"(|(cn={escaped_username})(uid={escaped_username}))",
        ["givenName", "sn", "mail"],
    )
    if not results:
        return None

    attributes = results[0][1] or {}

    def _decode_first(key: str) -> str:
        values = attributes.get(key)
        if not values:
            return ""
        value = values[0]
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore")
        return str(value)

    return LdapProfile(
        first_name=_decode_first("givenName"),
        last_name=_decode_first("sn"),
        email=_decode_first("mail"),
    )


def authenticate_ldap_user(username: str, password: str, config: AuthConfig) -> LdapAuthResult:
    """Authenticate a user against LDAP and optionally load profile fields."""

    if not username or not password or not config.ldap_server or not config.ldap_userdn:
        return LdapAuthResult(authenticated=False)

    ldap = _load_ldap_module()
    if ldap is None:
        return LdapAuthResult(authenticated=False)

    lookup_client = None
    client = None
    try:
        lookup_client = _initialize_client(ldap, config)
        bind_username = _build_bind_username(lookup_client, ldap, username, config)
        if not bind_username:
            return LdapAuthResult(authenticated=False)

        client = _initialize_client(ldap, config)
        client.simple_bind_s(bind_username, password)
        profile = (
            _search_profile(client, ldap, username, config) if config.ldap_update_on_login else None
        )
        logger.info("LDAP authentication succeeded for %s", username)
        return LdapAuthResult(authenticated=True, profile=profile)
    except Exception as exc:
        logger.info("LDAP authentication failed for %s: %s", username, exc)
        return LdapAuthResult(authenticated=False)
    finally:
        if client is not None:
            _unbind(client)
        if lookup_client is not None:
            _unbind(lookup_client)


def load_ldap_user_profile(
    username: str,
    config: AuthConfig,
    *,
    password: str = "",
) -> LdapProfile | None:
    """Fetch LDAP profile fields for an existing CRITs user."""

    if not username or not config.ldap_server or not config.ldap_userdn:
        return None

    ldap = _load_ldap_module()
    if ldap is None:
        return None

    client = None
    lookup_client = None
    try:
        if config.ldap_bind_dn:
            client = _initialize_client(ldap, config)
            client.simple_bind_s(config.ldap_bind_dn, config.ldap_bind_password)
            return _search_profile(client, ldap, username, config)

        if password:
            lookup_client = _initialize_client(ldap, config)
            bind_username = _build_bind_username(lookup_client, ldap, username, config)
            if not bind_username:
                return None

            client = _initialize_client(ldap, config)
            client.simple_bind_s(bind_username, password)
            return _search_profile(client, ldap, username, config)

        client = _initialize_client(ldap, config)
        return _search_profile(client, ldap, username, config)
    except Exception as exc:
        logger.info("LDAP profile lookup failed for %s: %s", username, exc)
        return None
    finally:
        if client is not None:
            _unbind(client)
        if lookup_client is not None:
            _unbind(lookup_client)
