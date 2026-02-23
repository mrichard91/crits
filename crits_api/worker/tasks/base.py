"""Base Celery task with retry policy, DB connection check, and logging."""

import logging

from celery import Task

from crits_api.db.connection import is_connected

logger = logging.getLogger(__name__)


class CRITsTask(Task):
    """Base task class for all CRITs worker tasks.

    Provides:
    - Automatic DB connection verification before execution
    - Structured logging on start/success/failure
    - Default retry policy with exponential backoff
    """

    autoretry_for = (ConnectionError, OSError)
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True
    max_retries = 3

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        """Verify DB connection before task execution."""
        if not is_connected():
            from crits_api.db.connection import connect_mongodb

            logger.info("Reconnecting to MongoDB from worker task")
            connect_mongodb()
        logger.debug("Task %s starting: %s args=%s", self.name, task_id, args)

    def on_success(self, retval: object, task_id: str, args: tuple, kwargs: dict) -> None:
        """Log successful task completion."""
        logger.info("Task %s completed: %s", self.name, task_id)

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: object,
    ) -> None:
        """Log task failure."""
        logger.error("Task %s failed: %s — %s", self.name, task_id, exc)

    def on_retry(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: object,
    ) -> None:
        """Log task retry."""
        logger.warning(
            "Task %s retrying (%d/%d): %s — %s",
            self.name,
            self.request.retries,
            self.max_retries,
            task_id,
            exc,
        )
