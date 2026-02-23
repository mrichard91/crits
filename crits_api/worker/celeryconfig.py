"""Celery configuration for CRITs worker.

Uses Redis DB 1 as broker/backend (DB 0 is used for Django caching/sessions).
"""

import os
import re

# Derive broker URL from REDIS_URL by swapping DB 0 -> DB 1
_redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
_broker_url = re.sub(r"/\d+$", "/1", _redis_url)

# Broker
broker_url = _broker_url
result_backend = _broker_url

# Serialization — JSON only (no pickle for security)
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# Timezone
timezone = "UTC"
enable_utc = True

# Task execution
task_acks_late = True
worker_prefetch_multiplier = 1
task_reject_on_worker_lost = True

# Result expiry (24 hours)
result_expires = 86400

# Task routing
task_routes = {
    "crits_api.worker.tasks.analysis.*": {"queue": "analysis"},
}

# Default queue
task_default_queue = "default"

# Autodiscover tasks in these modules
imports = [
    "crits_api.worker.tasks.analysis",
]

# Retry policy defaults
task_annotations = {
    "crits_api.worker.tasks.analysis.run_service_task": {
        "max_retries": 3,
        "default_retry_delay": 10,
    },
    "crits_api.worker.tasks.analysis.run_triage_task": {
        "max_retries": 1,
        "default_retry_delay": 5,
    },
}
