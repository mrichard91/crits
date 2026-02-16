"""Authentication mutation resolvers (login/logout)."""

import logging
import os

import strawberry
from strawberry.types import Info

from crits_api.auth.context import GraphQLContext

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
        from django.contrib.sessions.backends.cache import SessionStore

        from crits.config.config import CRITsConfig
        from crits.core.totp import valid_totp
        from crits.core.user import CRITsAuthBackend, EmbeddedLoginAttempt
        from crits.core.user_tools import save_user_secret

        ctx: GraphQLContext = info.context
        request = ctx.request
        error_msg = "Unknown user or bad password."

        # Extract request metadata for login tracking
        user_agent = request.headers.get("user-agent", "")
        remote_addr = request.client.host if request.client else ""
        accept_language = request.headers.get("accept-language", "")

        # Load CRITs config
        crits_config = CRITsConfig.objects().first()
        if not crits_config:
            return LoginResult(
                success=False,
                message=error_msg,
                status="login_failed",
            )

        totp = crits_config.totp_web

        # Authenticate via CRITsAuthBackend (handles LDAP, brute force, lockout)
        user = CRITsAuthBackend().authenticate(
            username=username,
            password=password,
            user_agent=user_agent,
            remote_addr=remote_addr,
            accept_language=accept_language,
            totp_enabled=totp,
        )

        if not user:
            return LoginResult(
                success=False,
                message=error_msg,
                status="login_failed",
            )

        # TOTP handling
        if totp == "Required" or (totp == "Optional" and user.totp):
            if not totp_pass:
                return LoginResult(
                    success=False,
                    message="TOTP required",
                    status="totp_required",
                )

            secret = user.secret
            if not secret and not totp_pass:
                return LoginResult(
                    success=False,
                    message="You have no TOTP secret. Please enter a new PIN in the TOTP field.",
                    status="no_secret",
                )
            elif not secret and totp_pass:
                # Generate new secret
                res = save_user_secret(username, totp_pass, "crits", (200, 200))
                if res["success"]:
                    user.reload()
                    totp_secret = res["secret"]
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
            elif not valid_totp(username, totp_pass, secret):
                # Invalid TOTP - track the failed attempt
                e = EmbeddedLoginAttempt(
                    user_agent=user_agent,
                    remote_addr=remote_addr,
                    accept_language=accept_language,
                )
                e.success = False
                user.login_attempts.append(e)
                user.invalid_login_attempts += 1
                user.save()
                return LoginResult(
                    success=False,
                    message=error_msg,
                    status="login_failed",
                )

            # TOTP valid - track successful attempt
            e = EmbeddedLoginAttempt(
                user_agent=user_agent,
                remote_addr=remote_addr,
                accept_language=accept_language,
            )
            e.success = True
            user.login_attempts.append(e)
            user.save()

        # Final login steps
        if not user.is_active:
            logger.info("Attempted login to a disabled account: %s", user.username)
            return LoginResult(
                success=False,
                message=error_msg,
                status="login_failed",
            )

        user.get_access_list(update=True)
        user.invalid_login_attempts = 0
        user.password_reset.reset_code = ""
        user.save()

        # Create Django session
        session_timeout = crits_config.session_timeout * 60 * 60  # hours to seconds
        store = SessionStore()
        store["_auth_user_id"] = str(user.id)
        store.set_expiry(session_timeout)
        store.create()

        # Set session cookie on response
        if ctx.response:
            secure = _get_secure_cookie()
            ctx.response.set_cookie(
                key="sessionid",
                value=store.session_key,
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
        from django.contrib.sessions.backends.cache import SessionStore

        ctx: GraphQLContext = info.context
        session_key = ctx.request.cookies.get("sessionid")

        if session_key:
            try:
                store = SessionStore(session_key=session_key)
                store.delete()
            except Exception as e:
                logger.warning("Error deleting session: %s", e)

        if ctx.response:
            ctx.response.delete_cookie("sessionid", path="/")

        logger.info("User logged out")
        return LogoutResult(success=True, message="Logged out successfully")
