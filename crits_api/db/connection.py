"""
MongoDB connection management for CRITs GraphQL API.

Uses MongoEngine (shared with Django) for database access.
This allows both Django and FastAPI to use the same models.

NOTE: We let Django handle the MongoDB connection via crits/settings.py
to avoid connection alias conflicts. This module just sets up Django.
"""

import logging
import os

logger = logging.getLogger(__name__)

# Track setup state
_django_setup = False


def connect_mongodb() -> None:
    """
    Initialize Django and let it handle MongoDB connection.

    Django's settings.py already handles MongoEngine connection,
    so we just need to ensure Django is set up.
    """
    global _django_setup

    if _django_setup:
        logger.debug("Django already set up")
        return

    try:
        # Set Django settings module
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crits.settings")

        # Import and setup Django - this will connect to MongoDB
        import django

        django.setup()

        _django_setup = True
        logger.info("Django initialized - MongoDB connection established via crits.settings")
    except Exception as e:
        logger.error(f"Error setting up Django: {e}")
        raise


def is_connected() -> bool:
    """Check if Django/MongoDB is set up."""
    return _django_setup
