"""CRITs Celery worker package."""

from crits_api.worker.app import celery_app

__all__ = ["celery_app"]
