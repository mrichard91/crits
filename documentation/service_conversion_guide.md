# CRITs Service Conversion Guide

How to port legacy `Service` subclasses to the modern `AnalysisService` architecture.

## Architecture overview

| | Legacy | Modern |
|---|---|---|
| Base class | `crits.services.core.Service` | `crits_api.worker.services.base.AnalysisService` |
| Registration | `ServiceManager.__subclasses__()` walk | `@register_service` decorator |
| Entry point | `run(self, obj, config)` | `run(self, context, config)` |
| Results | `self._add_result(subtype, result, data)` | `context.add_result(subtype, result, data)` |
| Logging | `self._info(msg)`, `self._error(msg)` | `context.info(msg)`, `context.error_log(msg)` |
| Config | `dict` from MongoDB + `ServiceConfigOption` | `ServiceConfig` dataclass |
| Object access | `obj` (MongoEngine document passed directly) | `context.obj` (same document, accessed via context) |
| File data | `obj.filedata.read()` | `context.get_file_data()` |
| Execution | `ServiceManager` + `handlers.run_service()` | Celery task via `execute_service()` |
| Triage flag | `is_triage_run = True` | `run_on_triage = True` |
| Validation | `valid_for(obj)` staticmethod | `validate_target(self, context)` instance method |
| Type check | `supported_for_type(type_)` classmethod | `supports_type(obj_type)` classmethod |
| Error signal | `self._error(msg)` (marks task as ERROR) | `context.error_log(msg)` + `context.status = "error"` |

## Step-by-step conversion

### 1. Change the imports and decorator

**Before:**
```python
from crits.services.core import Service, ServiceConfigOption

class MyService(Service):
    name = "my_service"
    version = "1.0.0"
    ...
```

**After:**
```python
from crits_api.worker.services.base import AnalysisService, AnalysisContext, ServiceConfig
from crits_api.worker.services.registry import register_service

@register_service
class MyService(AnalysisService):
    name = "my_service"
    version = "1.0.0"
    ...
```

The `@register_service` decorator replaces the `ServiceManager` discovery. When the module is imported, the decorator fires and the service is registered in the global registry.

### 2. Update class attributes

| Legacy attribute | Modern attribute | Notes |
|---|---|---|
| `name` | `name` | Same |
| `version` | `version` | Same |
| `description` | `description` | Same |
| `supported_types` | `supported_types` | Same format: `["Sample", "PCAP"]` or `["all"]` |
| `is_triage_run` | `run_on_triage` | Renamed |
| `type_` | *(removed)* | No longer used |
| `required_fields` | *(removed)* | Handle in `validate_target()` instead |
| `compatability_mode` | *(removed)* | Celery handles concurrency |
| `template` | *(removed)* | React UI renders results generically |
| `distributed` | *(removed)* | All services are non-distributed now |
| `source` | *(removed)* | Set at the execution pipeline level |
| `default_config` | `config_class` | See [Configuration](#5-convert-configuration) |

### 3. Convert `run(self, obj, config)` to `run(self, context, config)`

The signature changes from receiving a raw MongoEngine document to receiving an `AnalysisContext` wrapper.

**Before:**
```python
def run(self, obj, config):
    data = obj.filedata.read()
    self._info("Analyzing %d bytes" % len(data))
    self._add_result("finding", "something", {"key": "value"})
```

**After:**
```python
def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
    data = context.get_file_data()
    if not data:
        context.error_log("Could not read file data")
        context.status = "error"
        return
    context.info(f"Analyzing {len(data)} bytes")
    context.add_result("finding", "something", {"key": "value"})
```

Key differences:

- **Object access:** Use `context.obj` instead of bare `obj`. The underlying MongoEngine document is the same.
- **File data:** Use `context.get_file_data()` instead of `obj.filedata.read()`. It handles seek/read and error logging for you. Returns `None` on failure.
- **Results:** `self._add_result(...)` becomes `context.add_result(...)`. Same arguments: `(subtype, result, data=None)`.
- **Bulk results:** `self._add_results(results_list)` has no direct equivalent. Loop and call `context.add_result()` for each, or append directly to `context.results`.
- **Logging:** All `self._info/debug/warning` calls become `context.info/debug/warning`.
- **Errors:** `self._error(msg)` both logged and marked the task as ERROR. In the new system these are separate actions: call `context.error_log(msg)` to log, then set `context.status = "error"` to signal failure. The execution pipeline checks `context.status` after `run()` returns.
- **`self._critical(msg)`:** No direct equivalent. Use `context.error_log(msg)` + `context.status = "error"`.

### 4. Convert `valid_for()` to `validate_target()`

**Before:**
```python
@staticmethod
def valid_for(obj):
    if not obj.filedata:
        raise ServiceConfigError("Need filedata")
```

**After:**
```python
def validate_target(self, context: AnalysisContext) -> bool:
    if not self.supports_type(context.obj_type):
        return False
    if not hasattr(context.obj, "filedata") or not context.obj.filedata:
        context.info("No file data available, skipping")
        return False
    return True
```

Differences:
- Instance method, not staticmethod. Has access to `self` (the service instance).
- Returns `bool` instead of raising exceptions. `True` = proceed, `False` = skip.
- Always check `supports_type()` first. The old system did this externally; now it's the service's responsibility.
- Log a reason via `context.info()` when returning `False` so operators can see why the service was skipped.

### 5. Convert configuration

**Before (ServiceConfigOption):**
```python
from crits.services.core import Service, ServiceConfigOption

class MyService(Service):
    name = "my_service"
    default_config = [
        ServiceConfigOption('api_key',
                            ServiceConfigOption.STRING,
                            description="API key",
                            default="",
                            required=True,
                            private=True),
        ServiceConfigOption('timeout',
                            ServiceConfigOption.INT,
                            description="Timeout in seconds",
                            default=30),
    ]

    def run(self, obj, config):
        key = config['api_key']
        timeout = config['timeout']
```

**After (ServiceConfig dataclass):**
```python
from dataclasses import dataclass
from crits_api.worker.services.base import AnalysisService, AnalysisContext, ServiceConfig
from crits_api.worker.services.registry import register_service

@dataclass
class MyServiceConfig(ServiceConfig):
    api_key: str = ""
    timeout: int = 30

@register_service
class MyService(AnalysisService):
    name = "my_service"
    config_class = MyServiceConfig

    def run(self, context: AnalysisContext, config: MyServiceConfig) -> None:
        key = config.api_key        # attribute access, not dict
        timeout = config.timeout
```

Key differences:
- Config is a Python `dataclass`, not a list of `ServiceConfigOption` objects.
- Access values as attributes (`config.api_key`) not dict keys (`config['api_key']`).
- Type checking comes from dataclass field annotations.
- Set `config_class = MyServiceConfig` on the service class so the execution pipeline knows how to build it.
- No `private` / `required` / UI-rendering concerns — the React UI and GraphQL API handle presentation separately.

If your service has no configuration, omit `config_class` entirely (it defaults to the base `ServiceConfig`).

### 6. Convert `parse_config` / `validate_runtime`

These static methods validated configuration in the old system. In the new system, validation happens in two places:

1. **Dataclass `__post_init__`** for field-level validation:
```python
@dataclass
class MyServiceConfig(ServiceConfig):
    api_key: str = ""

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("api_key is required")
```

2. **`validate_target()`** for runtime validation that depends on the target object.

### 7. Remove legacy boilerplate

Delete these methods if your old service defined them — they have no equivalent and are not needed:

- `get_config()` / `get_config_details()` — config is a dataclass now
- `generate_config_form()` / `generate_runtime_form()` — React UI handles forms
- `bind_runtime_form()` — no form binding
- `save_runtime_config()` — config is passed directly
- `_notify()` — Celery handles task status; use logging instead
- `_write_to_file()` — use `tempfile` directly if you need temp files

### 8. Handle optional dependencies

If your service depends on a library that may not be installed, check at import time and gate in `validate_target()`:

```python
try:
    import pefile
    _PEFILE_AVAILABLE = True
except ImportError:
    _PEFILE_AVAILABLE = False

@register_service
class PEInfoService(AnalysisService):
    name = "peinfo"
    ...

    def validate_target(self, context: AnalysisContext) -> bool:
        if not _PEFILE_AVAILABLE:
            context.warning("pefile is not installed")
            return False
        ...
        return True

    def run(self, context: AnalysisContext, config: ServiceConfig) -> None:
        if not _PEFILE_AVAILABLE:
            context.error_log("pefile is not installed")
            context.status = "error"
            return
        ...
```

## Full conversion example

### Before: legacy VirusTotal service

```python
import logging
import requests

from crits.services.core import Service, ServiceConfigOption

logger = logging.getLogger(__name__)


class VirusTotalService(Service):
    name = "virustotal"
    version = "2.0.0"
    description = "Look up a sample hash on VirusTotal"
    supported_types = ["Sample"]
    is_triage_run = False
    required_fields = ["md5"]

    default_config = [
        ServiceConfigOption('vt_api_key',
                            ServiceConfigOption.STRING,
                            description="VirusTotal API key",
                            required=True,
                            private=True),
        ServiceConfigOption('vt_timeout',
                            ServiceConfigOption.INT,
                            description="Request timeout",
                            default=30),
    ]

    @staticmethod
    def valid_for(obj):
        if not hasattr(obj, 'md5') or not obj.md5:
            raise ServiceConfigError("Object has no MD5 hash")

    def run(self, obj, config):
        api_key = config['vt_api_key']
        timeout = config['vt_timeout']

        self._info("Looking up MD5: %s" % obj.md5)

        try:
            resp = requests.get(
                "https://www.virustotal.com/vtapi/v2/file/report",
                params={"apikey": api_key, "resource": obj.md5},
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            self._error("VT request failed: %s" % e)
            return

        if data.get("response_code") == 1:
            self._add_result("positives", str(data["positives"]), {
                "total": data["total"],
                "permalink": data["permalink"],
            })
            for av, result in data.get("scans", {}).items():
                if result.get("detected"):
                    self._add_result("av_detection", result["result"], {
                        "engine": av,
                    })
            self._info("VT lookup complete: %d/%d" % (data["positives"], data["total"]))
        else:
            self._info("Sample not found on VirusTotal")
```

### After: modern VirusTotal service

```python
import logging
from dataclasses import dataclass

import requests

from crits_api.worker.services.base import AnalysisContext, AnalysisService, ServiceConfig
from crits_api.worker.services.registry import register_service

logger = logging.getLogger(__name__)


@dataclass
class VirusTotalConfig(ServiceConfig):
    vt_api_key: str = ""
    vt_timeout: int = 30


@register_service
class VirusTotalService(AnalysisService):
    name = "virustotal"
    version = "2.0.0"
    description = "Look up a sample hash on VirusTotal"
    supported_types = ["Sample"]
    run_on_triage = False
    config_class = VirusTotalConfig

    def validate_target(self, context: AnalysisContext) -> bool:
        if not self.supports_type(context.obj_type):
            return False
        if not hasattr(context.obj, "md5") or not context.obj.md5:
            context.info("Object has no MD5 hash, skipping VT lookup")
            return False
        return True

    def run(self, context: AnalysisContext, config: VirusTotalConfig) -> None:
        if not config.vt_api_key:
            context.error_log("VirusTotal API key not configured")
            context.status = "error"
            return

        md5 = context.obj.md5
        context.info(f"Looking up MD5: {md5}")

        try:
            resp = requests.get(
                "https://www.virustotal.com/vtapi/v2/file/report",
                params={"apikey": config.vt_api_key, "resource": md5},
                timeout=config.vt_timeout,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            context.error_log(f"VT request failed: {e}")
            context.status = "error"
            return

        if data.get("response_code") == 1:
            context.add_result("positives", str(data["positives"]), {
                "total": data["total"],
                "permalink": data["permalink"],
            })
            for av, result in data.get("scans", {}).items():
                if result.get("detected"):
                    context.add_result("av_detection", result["result"], {
                        "engine": av,
                    })
            context.info(f"VT lookup complete: {data['positives']}/{data['total']}")
        else:
            context.info("Sample not found on VirusTotal")
```

## Deployment

### File structure

Place converted services in the `services/` directory at the repo root (mounted into the worker container at `/opt/crits_services`):

```
services/
├── virustotal_service/
│   ├── __init__.py          # contains @register_service class
│   └── requirements.txt     # optional: extra pip dependencies
├── peinfo_service/
│   └── __init__.py
└── ...
```

The worker scans directories listed in the `SERVICE_DIRS` environment variable (colon-separated). The default Docker Compose config sets `SERVICE_DIRS=/opt/crits_services`.

### Installing extra dependencies

If your service requires packages not in the base worker image, add them to the worker Dockerfile or install them at container startup. For development, you can exec into the container:

```bash
docker compose exec worker uv pip install pefile requests
```

For production, extend `docker/Dockerfile.worker`:

```dockerfile
# Install service dependencies
COPY services/virustotal_service/requirements.txt /tmp/vt-requirements.txt
RUN uv pip install -r /tmp/vt-requirements.txt
```

### Verifying

```bash
# Check worker logs for registration
docker compose logs worker | grep "Loaded external service package"
docker compose logs worker | grep "Registered service"

# List services via GraphQL
curl -s https://localhost:8443/api/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ listServices { name version description } }"}' | jq

# Run the service
curl -s https://localhost:8443/api/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { runService(serviceName: \"virustotal\", objType: \"Sample\", objId: \"<id>\") { success message } }"}' | jq
```

## Quick-reference conversion checklist

- [ ] Replace `from crits.services.core import Service` with modern imports
- [ ] Add `@register_service` decorator to the class
- [ ] Change base class from `Service` to `AnalysisService`
- [ ] Rename `is_triage_run` to `run_on_triage`
- [ ] Remove `type_`, `required_fields`, `compatability_mode`, `template`, `distributed`, `source`
- [ ] Remove `default_config` list; create a `ServiceConfig` dataclass if config is needed
- [ ] Set `config_class = MyConfig` on the service class
- [ ] Change `run(self, obj, config)` to `run(self, context, config)`
- [ ] Replace `obj` with `context.obj`; replace `obj.filedata.read()` with `context.get_file_data()`
- [ ] Replace `self._add_result(...)` with `context.add_result(...)`
- [ ] Replace `self._info/debug/warning(msg)` with `context.info/debug/warning(msg)`
- [ ] Replace `self._error(msg)` with `context.error_log(msg)` + `context.status = "error"`
- [ ] Replace `config['key']` dict access with `config.key` attribute access
- [ ] Convert `valid_for(obj)` to `validate_target(self, context)` returning `bool`
- [ ] Remove `parse_config`, `get_config`, form-generation methods, `_notify()`, `_write_to_file()`
- [ ] Place service in `services/<service_name>/__init__.py`
