"""Celery app factory with Django/MongoEngine bootstrap."""

import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)


def _bootstrap_django() -> None:
    """Initialize Django settings and MongoEngine connection."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crits_api.db.api_settings")
    import django

    django.setup()


# Bootstrap Django before creating the Celery app so models are available
_bootstrap_django()

celery_app = Celery("crits_worker")
celery_app.config_from_object("crits_api.worker.celeryconfig")

# Autodiscover tasks in worker.tasks package
celery_app.autodiscover_tasks(["crits_api.worker.tasks"])

logger.info("CRITs Celery app initialized")
