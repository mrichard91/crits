"""Celery app factory with lazy legacy-model bootstrap."""

import logging

from celery import Celery

logger = logging.getLogger(__name__)

celery_app = Celery("crits_worker")
celery_app.config_from_object("crits_api.worker.celeryconfig")

# Autodiscover tasks in worker.tasks package
celery_app.autodiscover_tasks(["crits_api.worker.tasks"])

logger.info("CRITs Celery app initialized; legacy model bootstrap deferred to task startup")
