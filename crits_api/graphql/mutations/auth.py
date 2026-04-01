"""Authentication mutation resolvers (login/logout)."""

import logging
import os
from datetime import datetime

import strawberry
from django.contrib.auth.hashers import check_password
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext
from crits_api.auth.ldap import authenticate_ldap_user, load_ldap_user_profile
from crits_api.auth.redis_session import create_session, delete_session
from crits_api.auth.totp import gen_user_secret, valid_totp
from crits_api.config import settings
from crits_api.db.auth_records import (
    AuthConfig,
    AuthUserRecord,
    get_auth_config,
    get_auth_user_by_username,
    update_auth_user_by_id,
    update_auth_user_by_username,
)

logger = logging.getLogger(__name__)


@strawberry.type
class LoginResult:
    success: bool
    message: str
    status: str
    totp_secret: str | None = None


@strawberry.type
class LogoutResult:
    success: bool
    message: str


def _get_secure_cookie() -> bool:
    """Read SECURE_COOKIES env var, matching Django settings.py:91 behavior."""

    return os.environ.get("SECURE_COOKIES", "true").lower() in ("true", "1", "yes")


def _login_attempt(
    *,
    success: bool,
    user_agent: str,
    remote_addr: str,
    accept_language: str,
) -> dict[str, object]:
    return {
        "success": success,
        "user_agent": user_agent,
        "remote_addr": remote_addr,
        "accept_language": accept_language,
        "date": datetime.now(),
    }


def _totp_required(totp_setting: str, user: AuthUserRecord) -> bool:
    """Return whether this login attempt requires a TOTP token."""

    return totp_setting == "Required" or (totp_setting == "Optional" and user.totp)


def _exceeded_totp_retry_threshold(user: AuthUserRecord, interval_seconds: int = 10) -> bool:
    """Throttle repeated failed TOTP attempts to match legacy auth behavior."""

    if not user.login_attempts:
        return False

    last_attempt = user.login_attempts[-1]
    if bool(last_attempt.get("success", False)):
        return False

    last_attempt_date = last_attempt.get("date")
    if not isinstance(last_attempt_date, datetime):
        return False

    return (datetime.now() - last_attempt_date).total_seconds() < interval_seconds


def _record_failed_password_attempt(
    user: AuthUserRecord,
    *,
    auth_config: AuthConfig,
    user_agent: str,
    remote_addr: str,
    accept_language: str,
) -> None:
    """Record a failed password-based login attempt and disable the account if needed."""

    failed_attempt_count = user.invalid_login_attempts + 1
    set_fields: dict[str, object] = {"invalid_login_attempts": failed_attempt_count}
    if user.is_active and failed_attempt_count > auth_config.invalid_login_threshold:
        set_fields["is_active"] = False
        logger.info(
            "Account disabled due to too many invalid login attempts: %s",
            user.username,
        )

    update_auth_user_by_id(
        user.id,
        set_fields=set_fields,
        append_login_attempt=_login_attempt(
            success=False,
            user_agent=user_agent,
            remote_addr=remote_addr,
            accept_language=accept_language,
        ),
    )


def _handle_totp_step(
    *,
    user: AuthUserRecord,
    username: str,
    totp_setting: str,
    totp_pass: str | None,
    user_agent: str,
    remote_addr: str,
    accept_language: str,
    error_msg: str,
) -> LoginResult | None:
    """Handle TOTP validation or enrollment for a successful primary auth step."""

    if not _totp_required(totp_setting, user):
        return None

    if not totp_pass:
        return LoginResult(
            success=False,
            message="TOTP required",
            status="totp_required",
        )

    if not user.secret:
        encrypted_secret, totp_secret = gen_user_secret(totp_pass, username)
        updated_user = update_auth_user_by_username(
            username,
            set_fields={"secret": encrypted_secret, "totp": True},
        )
        if updated_user:
            message = f"Setup your authenticator using: '{totp_secret}'"
            message += " Then authenticate again with your PIN + token."
            return LoginResult(
                success=False,
                message=message,
                status="secret_generated",
                totp_secret=totp_secret,
            )
        return LoginResult(
            success=False,
            message="Secret generation failed",
            status="secret_generated",
        )

    if valid_totp(username, totp_pass, user.secret):
        return None

    update_auth_user_by_id(
        user.id,
        set_fields={"invalid_login_attempts": user.invalid_login_attempts + 1},
        append_login_attempt=_login_attempt(
            success=False,
            user_agent=user_agent,
            remote_addr=remote_addr,
            accept_language=accept_language,
        ),
    )
    return LoginResult(
        success=False,
        message=error_msg,
        status="login_failed",
    )


@strawberry.type
class AuthMutations:
    @strawberry.mutation(description="Authenticate a user and create a session")
    def login(
        self,
        info: Info,
        username: str,
        password: str,
        totp_pass: str | None = None,
    ) -> LoginResult:
        ctx: GraphQLContext = info.context
        request = ctx.request
        error_msg = "Unknown user or bad password."

        user_agent = request.headers.get("user-agent", "")
        remote_addr = request.client.host if request.client else ""
        accept_language = request.headers.get("accept-language", "")

        auth_config = get_auth_config()
        user = get_auth_user_by_username(username)

        if not user:
            return LoginResult(
                success=False,
                message=error_msg,
                status="login_failed",
            )

        if auth_config.ldap_auth:
            if _totp_required(auth_config.totp_web, user) and _exceeded_totp_retry_threshold(user):
                update_auth_user_by_id(
                    user.id,
                    append_login_attempt=_login_attempt(
                        success=False,
                        user_agent=user_agent,
                        remote_addr=remote_addr,
                        accept_language=accept_language,
                    ),
                )
                return LoginResult(
                    success=False,
                    message=error_msg,
                    status="login_failed",
                )

            ldap_result = authenticate_ldap_user(username, password, auth_config)
            if ldap_result.authenticated:
                if ldap_result.profile is not None:
                    update_auth_user_by_username(
                        username,
                        set_fields=ldap_result.profile.as_update_fields(),
                    )
            elif not password or not check_password(password, user.password):
                _record_failed_password_attempt(
                    user,
                    auth_config=auth_config,
                    user_agent=user_agent,
                    remote_addr=remote_addr,
                    accept_language=accept_language,
                )
                return LoginResult(
                    success=False,
                    message=error_msg,
                    status="login_failed",
                )
            elif auth_config.ldap_update_on_login:
                profile = load_ldap_user_profile(username, auth_config)
                if profile is not None:
                    update_auth_user_by_username(
                        username,
                        set_fields=profile.as_update_fields(),
                    )
        elif not password or not check_password(password, user.password):
            _record_failed_password_attempt(
                user,
                auth_config=auth_config,
                user_agent=user_agent,
                remote_addr=remote_addr,
                accept_language=accept_language,
            )
            return LoginResult(
                success=False,
                message=error_msg,
                status="login_failed",
            )

        totp_result = _handle_totp_step(
            user=user,
            username=username,
            totp_setting=auth_config.totp_web,
            totp_pass=totp_pass,
            user_agent=user_agent,
            remote_addr=remote_addr,
            accept_language=accept_language,
            error_msg=error_msg,
        )
        if totp_result is not None:
            return totp_result

        if not user.is_active:
            logger.info("Attempted login to a disabled account: %s", user.username)
            return LoginResult(
                success=False,
                message=error_msg,
                status="login_failed",
            )

        update_auth_user_by_id(
            user.id,
            set_fields={
                "invalid_login_attempts": 0,
                "password_reset.reset_code": "",
                "acl_needs_update": user.acl_needs_update,
            },
            append_login_attempt=_login_attempt(
                success=True,
                user_agent=user_agent,
                remote_addr=remote_addr,
                accept_language=accept_language,
            ),
        )

        session_timeout = auth_config.session_timeout_hours * 60 * 60
        session_key = create_session(
            redis_url=settings.redis_url,
            user_id=str(user.id),
            ttl=session_timeout,
        )

        if ctx.response:
            secure = _get_secure_cookie()
            ctx.response.set_cookie(
                key="sessionid",
                value=session_key,
                path="/",
                httponly=True,
                samesite="lax",
                secure=secure,
                max_age=session_timeout,
            )

        logger.info("User %s logged in successfully", user.username)
        return LoginResult(
            success=True,
            message="Login successful",
            status="login_successful",
        )

    @strawberry.mutation(description="Destroy the current session and log out")
    def logout(self, info: Info) -> LogoutResult:
        ctx: GraphQLContext = info.context
        session_key = ctx.request.cookies.get("sessionid")

        if session_key:
            try:
                delete_session(
                    redis_url=settings.redis_url,
                    session_key=session_key,
                )
            except Exception as e:
                logger.warning("Error deleting session: %s", e)

        if ctx.response:
            ctx.response.delete_cookie("sessionid", path="/")

        logger.info("User logged out")
        return LogoutResult(success=True, message="Logged out successfully")
