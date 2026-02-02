"""
Configuration settings for CRITs GraphQL API.

Uses Pydantic settings for environment variable management.
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


def parse_cors_origins() -> list[str]:
    """Parse CORS_ORIGINS env var (comma-separated) into a list."""
    env_value = os.environ.get("CORS_ORIGINS", "")
    if env_value:
        return [origin.strip() for origin in env_value.split(",") if origin.strip()]
    return ["http://localhost:8080", "http://127.0.0.1:8080"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "CRITs GraphQL API"
    debug: bool = False

    # MongoDB
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_database: str = "crits"
    mongo_username: str | None = None
    mongo_password: str | None = None

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Cache settings
    cache_default_ttl: int = 900  # 15 minutes
    cache_enabled: bool = True

    # Django session settings (for session sharing)
    django_secret_key: str = "dev-secret-key-change-in-production"
    session_cookie_name: str = "sessionid"

    # GraphQL
    graphql_path: str = "/api/graphql"
    graphiql_enabled: bool = True  # Enable GraphiQL in dev
    query_depth_limit: int = 10
    query_complexity_limit: int = 100

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "env_file": ".env",
        "extra": "ignore",
    }

    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins from environment."""
        return parse_cors_origins()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience access
settings = get_settings()
