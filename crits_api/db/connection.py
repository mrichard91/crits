"""
MongoDB connection management for CRITs GraphQL API.

Uses MongoEngine (shared with Django) for database access.
This allows both Django and FastAPI to use the same models.

NOTE: We use a minimal API-specific settings module instead of the
full Django web config. crits/ models still need django.conf.settings
to be populated, so we still call django.setup() — but with a
stripped-down settings module that has no templates, middleware, URL
routing, views, or static files.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Track setup state
_django_setup = False


def connect_mongodb() -> None:
    """
    Initialize Django with minimal API settings and connect to MongoDB.

    Uses crits_api.db.api_settings instead of the full crits.settings
    to avoid loading the entire Django web framework config.
    """
    global _django_setup

    if _django_setup:
        logger.debug("Django already set up")
        return

    try:
        # Use the minimal API settings module instead of the full web config
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crits_api.db.api_settings")

        # Import and setup Django - this will connect to MongoDB
        import django

        django.setup()

        _django_setup = True
        logger.info(
            "Django initialized - MongoDB connection established via crits_api.db.api_settings"
        )
    except Exception as e:
        logger.error(f"Error setting up Django: {e}")
        raise


def is_connected() -> bool:
    """Check if Django/MongoDB is set up."""
    return _django_setup
