"""Minimal Django settings for the CRITs GraphQL API.

This provides only what crits/ models and handlers need from
django.conf.settings — no templates, middleware, URL routing,
views, or static files configuration.

Used by crits_api/db/connection.py as DJANGO_SETTINGS_MODULE.
"""

import errno
import os
import sys
from typing import Any

from mongoengine import connect
from pymongo import MongoClient, ReadPreference
from pymongo.database import Database

SITE_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "crits")

# Django requires these
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-change-in-production")
DEBUG = os.environ.get("DEBUG", "true").lower() in ("true", "1", "yes")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.dummy",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Redis cache — needed if any code touches Django's cache framework
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    },
}

# Minimal INSTALLED_APPS — only crits model apps + auth plumbing
INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "crits.core",
    "crits.dashboards",
    "crits.actors",
    "crits.campaigns",
    "crits.certificates",
    "crits.domains",
    "crits.emails",
    "crits.events",
    "crits.indicators",
    "crits.ips",
    "crits.locations",
    "crits.objects",
    "crits.pcaps",
    "crits.raw_data",
    "crits.relationships",
    "crits.samples",
    "crits.screenshots",
    "crits.services",
    "crits.signatures",
    "crits.stats",
    "crits.targets",
    "django_mongoengine",
    "django_mongoengine.mongo_auth",
)

AUTH_USER_MODEL = "mongo_auth.MongoUser"
MONGOENGINE_USER_DOCUMENT = "crits.core.user.CRITsUser"

# ---------------------------------------------------------------------------
# MongoDB configuration (mirrors crits/settings.py)
# ---------------------------------------------------------------------------
MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))
MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "crits")

# Required by django_mongoengine app
MONGODB_DATABASES = {
    "default": {
        "name": MONGO_DATABASE,
        "host": MONGO_HOST,
        "password": None,
        "username": None,
        "tz_aware": True,
    },
}
MONGO_SSL = os.environ.get("MONGO_SSL", "").lower() in ("true", "1", "yes")
MONGO_USER = os.environ.get("MONGO_USER", "")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD", "")
MONGO_REPLICASET = os.environ.get("MONGO_REPLICASET") or None
MONGO_READ_PREFERENCE = ReadPreference.PRIMARY

# File storage
S3 = "S3"
GRIDFS = "GRIDFS"
FILE_DB = GRIDFS
BUCKET_PCAPS = "pcaps"
BUCKET_OBJECTS = "objects"
BUCKET_SAMPLES = "samples"

# Import custom database config (same as crits/settings.py)
dbfile = os.path.join(SITE_ROOT, "config/database.py")
if os.path.exists(dbfile):
    with open(dbfile) as f:
        exec(compile(f.read(), dbfile, "exec"))

# MongoEngine connection
if MONGO_USER:
    connect(
        MONGO_DATABASE,
        host=MONGO_HOST,
        port=MONGO_PORT,
        read_preference=MONGO_READ_PREFERENCE,
        ssl=MONGO_SSL,
        replicaset=MONGO_REPLICASET,
        username=MONGO_USER,
        password=MONGO_PASSWORD,
    )
else:
    connect(
        MONGO_DATABASE,
        host=MONGO_HOST,
        port=MONGO_PORT,
        read_preference=MONGO_READ_PREFERENCE,
        ssl=MONGO_SSL,
        replicaset=MONGO_REPLICASET,
    )


# PyMongo connection (used by handlers via settings.PY_DB)
def _connect_pymongo(
    dbs: str = MONGO_DATABASE,
    dbhost: str = MONGO_HOST,
    dbport: int = MONGO_PORT,
    dbuser: str = MONGO_USER,
    dbpass: str = MONGO_PASSWORD,
    dbssl: bool = MONGO_SSL,
    w: int = 1,
) -> "Database[dict[str, Any]]":
    client: MongoClient[dict[str, Any]] = MongoClient(dbhost, dbport, ssl=dbssl, w=w)
    dbase = client[dbs]
    if dbuser:
        dbase.authenticate(dbuser, dbpass)
    return dbase


PY_DB = _connect_pymongo()

# ---------------------------------------------------------------------------
# Collection name constants
# ---------------------------------------------------------------------------
COL_ACTORS = "actors"
COL_ACTOR_IDENTIFIERS = "actor_identifiers"
COL_ACTOR_THREAT_IDENTIFIERS = "actor_threat_identifiers"
COL_ACTOR_THREAT_TYPES = "actor_threat_types"
COL_ACTOR_MOTIVATIONS = "actor_motivations"
COL_ACTOR_SOPHISTICATIONS = "actor_sophistications"
COL_ACTOR_INTENDED_EFFECTS = "actor_intended_effects"
COL_ANALYSIS_RESULTS = "analysis_results"
COL_AUDIT_LOG = "audit_log"
COL_BACKDOORS = "backdoors"
COL_BUCKET_LISTS = "bucket_lists"
COL_CAMPAIGNS = "campaigns"
COL_CERTIFICATES = "certificates"
COL_COMMENTS = "comments"
COL_CONFIG = "config"
COL_COUNTS = "counts"
COL_DIVISION_DATA = "division_data"
COL_DOMAINS = "domains"
COL_EFFECTIVE_TLDS = "effective_tlds"
COL_EMAIL = "email"
COL_EVENTS = "events"
COL_EVENT_TYPES = "event_types"
COL_EXPLOITS = "exploits"
COL_FILETYPES = "filetypes"
COL_IDB_ACTIONS = "idb_actions"
COL_INDICATORS = "indicators"
COL_IPS = "ips"
COL_LOCATIONS = "locations"
COL_NOTIFICATIONS = "notifications"
COL_OBJECTS = "objects"
COL_OBJECT_TYPES = "object_types"
COL_PCAPS = "pcaps"
COL_RAW_DATA = "raw_data"
COL_RAW_DATA_TYPES = "raw_data_types"
COL_RELATIONSHIP_TYPES = "relationship_types"
COL_ROLES = "roles"
COL_SAMPLES = "sample"
COL_SCREENSHOTS = "screenshots"
COL_SECTOR_LISTS = "sector_lists"
COL_SECTORS = "sectors"
COL_SERVICES = "services"
COL_SIGNATURE_TYPES = "signature_types"
COL_SIGNATURE_DEPENDENCY = "signature_dependency"
COL_SOURCE_ACCESS = "source_access"
COL_SOURCES = "sources"
COL_STATISTICS = "statistics"
COL_SIGNATURES = "signatures"
COL_TARGETS = "targets"
COL_USERS = "users"
COL_YARAHITS = "yarahits"

COLLECTION_TO_BUCKET_MAPPING = {
    COL_PCAPS: BUCKET_PCAPS,
    COL_OBJECTS: BUCKET_OBJECTS,
    COL_SAMPLES: BUCKET_SAMPLES,
}

# ---------------------------------------------------------------------------
# CRITs types registry
# ---------------------------------------------------------------------------
CRITS_TYPES = {
    "Actor": COL_ACTORS,
    "ActorIdentifier": COL_ACTOR_IDENTIFIERS,
    "AnalysisResult": COL_ANALYSIS_RESULTS,
    "Backdoor": COL_BACKDOORS,
    "Campaign": COL_CAMPAIGNS,
    "Certificate": COL_CERTIFICATES,
    "Comment": COL_COMMENTS,
    "Domain": COL_DOMAINS,
    "Email": COL_EMAIL,
    "Event": COL_EVENTS,
    "Exploit": COL_EXPLOITS,
    "Indicator": COL_INDICATORS,
    "IP": COL_IPS,
    "Notification": COL_NOTIFICATIONS,
    "PCAP": COL_PCAPS,
    "RawData": COL_RAW_DATA,
    "Sample": COL_SAMPLES,
    "Screenshot": COL_SCREENSHOTS,
    "Signature": COL_SIGNATURES,
    "Target": COL_TARGETS,
}

# ---------------------------------------------------------------------------
# Config from DB (mirrors crits/settings.py approach)
# ---------------------------------------------------------------------------
_coll = PY_DB[COL_CONFIG]
_crits_config = _coll.find_one({}) or {}

ADMIN_ROLE = "UberAdmin"
COMPANY_NAME = _crits_config.get("company_name", "My Company")
CLASSIFICATION = _crits_config.get("classification", "unclassified")
INSTANCE_NAME = _crits_config.get("instance_name", "My Instance")
INSTANCE_URL = _crits_config.get("instance_url", "")

# Auth / password settings
INVALID_LOGIN_ATTEMPTS = _crits_config.get("invalid_login_attempts", 3) - 1
PASSWORD_COMPLEXITY_REGEX = _crits_config.get(
    "password_complexity_regex",
    r"(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$",
)
PASSWORD_COMPLEXITY_DESC = _crits_config.get(
    "password_complexity_desc", "8 characters, at least 1 capital, 1 lowercase and 1 number/special"
)
SESSION_TIMEOUT = int(_crits_config.get("session_timeout", 12)) * 60 * 60
SECURE_COOKIE = _crits_config.get("secure_cookie", True)
TOTP = _crits_config.get("totp", False)

# Service settings
SERVICE_DIRS = tuple(_crits_config.get("service_dirs", []))
SERVICE_MODEL = _crits_config.get("service_model", "process")
SERVICE_POOL_SIZE = int(_crits_config.get("service_pool_size", 12))

# Datetime formats
PY_DATE_FORMAT = "%Y-%m-%d"
PY_TIME_FORMAT = "%H:%M:%S.%f"
PY_DATETIME_FORMAT = " ".join([PY_DATE_FORMAT, PY_TIME_FORMAT])
OLD_PY_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
PY_FORM_DATETIME_FORMATS = [PY_DATETIME_FORMAT, OLD_PY_DATETIME_FORMAT]

# Relationship traversal limits
DEPTH_MAX = _crits_config.get("depth_max", "10")
TOTAL_MAX = _crits_config.get("total_max", "250")
REL_MAX = _crits_config.get("rel_max", "50")

# Miscellaneous settings referenced by models/handlers
CRITS_VERSION = "4-master"
CRITS_EMAIL = _crits_config.get("crits_email", "")
CRITS_EMAIL_SUBJECT_TAG = _crits_config.get("crits_email_subject_tag", "")
CRITS_EMAIL_END_TAG = _crits_config.get("crits_email_end_tag", True)
DEVEL_INSTANCE = False
ENABLE_API = False
ENABLE_TOASTS = _crits_config.get("enable_toasts", False)
ENABLE_DT = False
GIT_HASH = ""
GIT_HASH_LONG = ""
GIT_BRANCH = ""
GIT_REPO_URL = _crits_config.get("git_repo_url", "")
HIDE_GIT_HASH = True
HTTP_PROXY = _crits_config.get("http_proxy", None)
LANGUAGE_CODE = _crits_config.get("language_code", "en-us")
LDAP_AUTH = _crits_config.get("ldap_auth", False)
LDAP_SERVER = _crits_config.get("ldap_server", "")
LDAP_BIND_DN = _crits_config.get("ldap_bind_dn", "")
LDAP_BIND_PASSWORD = _crits_config.get("ldap_bind_password", "")
LDAP_USERDN = _crits_config.get("ldap_userdn", "")
LDAP_USERCN = _crits_config.get("ldap_usercn", "")
QUERY_CACHING = _crits_config.get("query_caching", False)
REMOTE_USER = _crits_config.get("remote_user", False)
REMOTE_USER_META = "REMOTE_USER"
RT_URL = _crits_config.get("rt_url", None)
SPLUNK_SEARCH_URL = _crits_config.get("splunk_search_url", None)
TEMP_DIR = _crits_config.get("temp_dir", "/tmp")
TIME_ZONE = _crits_config.get("timezone", "America/New_York")
ZIP7_PATH = _crits_config.get("zip7_path", "/usr/bin/7z")
ZIP7_PASSWORD = _crits_config.get("zip7_password", "infected")

# Logging (minimal — no file handlers, just console)
LOG_DIRECTORY = _crits_config.get("log_directory", os.path.join(SITE_ROOT, "..", "logs"))
LOG_LEVEL = _crits_config.get("log_level", "INFO")

if not os.path.exists(LOG_DIRECTORY):
    LOG_DIRECTORY = os.path.join(SITE_ROOT, "..", "logs")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "normal": {
            "level": LOG_LEVEL,
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": os.path.join(LOG_DIRECTORY, "crits.log"),
        },
    },
    "loggers": {
        "django": {
            "handlers": ["normal"],
            "propagate": True,
            "level": "INFO",
        },
        "crits": {
            "handlers": ["normal"],
            "propagate": True,
            "level": "DEBUG",
        },
    },
}

_handlers: dict[str, dict[str, str]] = LOGGING["handlers"]  # type: ignore[assignment]
for handler in _handlers.values():
    log_file = handler.get("filename")
    if log_file:
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError as e:
                if e.args[0] != errno.EEXIST:
                    raise

# Service templates (empty — no UI in API)
SERVICE_NAV_TEMPLATES = ()
SERVICE_CP_TEMPLATES = ()
SERVICE_TAB_TEMPLATES = ()

# Discover service directories (handlers may import from them)
for service_directory in SERVICE_DIRS:
    if os.path.isdir(service_directory):
        sys.path.insert(0, service_directory)

# Media paths (referenced by some handlers)
MEDIA_ROOT = os.path.join(SITE_ROOT, "../extras/www")
MEDIA_URL = "/"
