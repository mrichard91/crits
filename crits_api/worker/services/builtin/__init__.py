"""Built-in analysis services.

Importing this package triggers registration of all built-in services.
"""

from crits_api.worker.services.builtin.filetype import FileTypeService
from crits_api.worker.services.builtin.hashes import HashCalculationService
from crits_api.worker.services.builtin.ssdeep_hash import SSDeepHashService
from crits_api.worker.services.builtin.yara_scan import YaraScanService

__all__ = [
    "FileTypeService",
    "HashCalculationService",
    "SSDeepHashService",
    "YaraScanService",
]
