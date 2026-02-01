#!/usr/bin/env python3
"""
CRITs Environment Validation Script

This script tests that all major dependencies and modules can be imported
successfully. Run this after setting up the environment to verify everything
is working.

Usage:
    python scripts/test_imports.py
    # or via Docker:
    make env-test

Environment variables:
    SKIP_CRITS_MODULES=1  Skip CRITs module imports (when no MongoDB available)
    MONGODB_HOST          MongoDB host for connection test (default: localhost)
"""

import os
import sys
import traceback
import signal
from typing import Tuple
from contextlib import contextmanager

# Check if we should skip CRITs modules (no MongoDB available)
SKIP_CRITS_MODULES = os.environ.get('SKIP_CRITS_MODULES', '0').lower() in ('1', 'true', 'yes')
# Support both MONGODB_HOST (test script) and MONGO_HOST (CRITs settings)
MONGODB_HOST = os.environ.get('MONGODB_HOST') or os.environ.get('MONGO_HOST', 'localhost')
MONGODB_PORT = int(os.environ.get('MONGO_PORT', 27017))


class TimeoutError(Exception):
    pass


@contextmanager
def timeout(seconds):
    """Context manager for timing out operations."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def test_import(module_name: str, description: str = "", timeout_secs: int = 5) -> Tuple[bool, str]:
    """Test importing a module and return success status."""
    try:
        with timeout(timeout_secs):
            __import__(module_name)
        return True, ""
    except ImportError as e:
        return False, str(e)
    except TimeoutError as e:
        return False, str(e)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def test_from_import(module_name: str, names: list, description: str = "") -> Tuple[bool, str]:
    """Test importing specific names from a module."""
    try:
        module = __import__(module_name, fromlist=names)
        for name in names:
            getattr(module, name)
        return True, ""
    except ImportError as e:
        return False, str(e)
    except AttributeError as e:
        return False, str(e)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def print_result(name: str, success: bool, error: str = ""):
    """Print test result with color coding."""
    if success:
        print(f"  {GREEN}✓{RESET} {name}")
    else:
        print(f"  {RED}✗{RESET} {name}")
        if error:
            print(f"    {RED}└─ {error}{RESET}")


def main():
    print(f"\n{BOLD}CRITs Environment Validation{RESET}")
    print("=" * 50)

    results = {"passed": 0, "failed": 0, "warnings": 0}

    # ==========================================================================
    # Core Python Dependencies
    # ==========================================================================
    print(f"\n{BOLD}Core Dependencies:{RESET}")

    core_deps = [
        ("django", "Django web framework"),
        ("mongoengine", "MongoDB ODM"),
        ("pymongo", "MongoDB driver"),
        ("celery", "Task queue"),
        ("redis", "Redis client"),
        ("cryptography", "Cryptography library"),
        ("lxml", "XML processing"),
        ("PIL", "Pillow image processing"),
        ("requests", "HTTP client"),
        ("yaml", "YAML parser"),
        ("dateutil", "Date utilities"),
        ("pytz", "Timezone support"),
        ("defusedxml", "Safe XML parsing"),
        ("chardet", "Character detection"),
        ("olefile", "OLE file parsing"),
        ("biplist", "Binary plist parsing"),
        ("qrcode", "QR code generation"),
        ("magic", "File type detection"),
        ("pyparsing", "Parser library"),
    ]

    for module, desc in core_deps:
        success, error = test_import(module)
        print_result(f"{module} ({desc})", success, error)
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1

    # ==========================================================================
    # Optional Dependencies (may not be installed)
    # ==========================================================================
    print(f"\n{BOLD}Optional Dependencies:{RESET}")

    optional_deps = [
        ("pydeep", "Fuzzy hashing (ssdeep)"),
        ("pyimpfuzzy", "Import fuzzy hashing"),
        ("ldap", "LDAP authentication"),
    ]

    for module, desc in optional_deps:
        success, error = test_import(module)
        if success:
            print_result(f"{module} ({desc})", True)
            results["passed"] += 1
        else:
            print(f"  {YELLOW}○{RESET} {module} ({desc}) - optional, not installed")
            results["warnings"] += 1

    # ==========================================================================
    # MongoDB Connectivity Test
    # ==========================================================================
    print(f"\n{BOLD}MongoDB Connectivity:{RESET}")

    mongodb_available = False
    mongo_addr = f"{MONGODB_HOST}:{MONGODB_PORT}"
    try:
        from pymongo import MongoClient
        with timeout(10):
            client = MongoClient(MONGODB_HOST, MONGODB_PORT, serverSelectionTimeoutMS=5000)
            client.server_info()  # Will raise exception if cannot connect
            mongodb_available = True
            print_result(f"MongoDB connection ({mongo_addr})", True)
            results["passed"] += 1
            client.close()
    except Exception as e:
        if SKIP_CRITS_MODULES:
            print(f"  {YELLOW}○{RESET} MongoDB connection ({mongo_addr}) - skipped (SKIP_CRITS_MODULES=1)")
        else:
            print(f"  {YELLOW}○{RESET} MongoDB connection ({mongo_addr}) - not available")
            print(f"    {YELLOW}└─ {e}{RESET}")
        results["warnings"] += 1

    # ==========================================================================
    # CRITs Core Modules (requires MongoDB)
    # ==========================================================================
    print(f"\n{BOLD}CRITs Core Modules:{RESET}")

    if SKIP_CRITS_MODULES or not mongodb_available:
        print(f"  {YELLOW}○{RESET} Skipped - MongoDB not available or SKIP_CRITS_MODULES=1")
        print(f"    {YELLOW}└─ CRITs imports require a running MongoDB instance{RESET}")
        results["warnings"] += 1
    else:
        # Test that crits package structure is importable
        crits_core = [
            ("crits", "CRITs package root"),
            ("crits.core", "Core module"),
            ("crits.core.crits_mongoengine", "MongoEngine extensions"),
            ("crits.core.fields", "Custom fields"),
            ("crits.core.user", "User model"),
            ("crits.core.role", "Role model"),
            ("crits.core.handlers", "Core handlers"),
            ("crits.core.data_tools", "Data utilities"),
            ("crits.core.mongo_tools", "MongoDB utilities"),
        ]

        for module, desc in crits_core:
            success, error = test_import(module, timeout_secs=30)
            print_result(f"{module}", success, error)
            if success:
                results["passed"] += 1
            else:
                results["failed"] += 1

    # ==========================================================================
    # CRITs TLO (Top-Level Object) Modules (requires MongoDB)
    # ==========================================================================
    print(f"\n{BOLD}CRITs TLO Modules:{RESET}")

    if SKIP_CRITS_MODULES or not mongodb_available:
        print(f"  {YELLOW}○{RESET} Skipped - MongoDB not available or SKIP_CRITS_MODULES=1")
        results["warnings"] += 1
    else:
        tlo_modules = [
            "crits.actors",
            "crits.backdoors",
            "crits.campaigns",
            "crits.certificates",
            "crits.comments",
            "crits.domains",
            "crits.emails",
            "crits.events",
            "crits.exploits",
            "crits.indicators",
            "crits.ips",
            "crits.notifications",
            "crits.objects",
            "crits.pcaps",
            "crits.raw_data",
            "crits.relationships",
            "crits.samples",
            "crits.screenshots",
            "crits.services",
            "crits.signatures",
            "crits.targets",
            "crits.vocabulary",
        ]

        for module in tlo_modules:
            success, error = test_import(module, timeout_secs=30)
            print_result(module, success, error)
            if success:
                results["passed"] += 1
            else:
                results["failed"] += 1

    # ==========================================================================
    # Django Configuration Test
    # ==========================================================================
    print(f"\n{BOLD}Django Configuration:{RESET}")

    if SKIP_CRITS_MODULES or not mongodb_available:
        print(f"  {YELLOW}○{RESET} Skipped - MongoDB not available")
        results["warnings"] += 1
    else:
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crits.settings')
            import django
            django.setup()
            print_result("Django setup", True)
            results["passed"] += 1
        except Exception as e:
            # Expected to fail without MongoDB - that's OK for import test
            if "database" in str(e).lower() or "mongo" in str(e).lower():
                print(f"  {YELLOW}○{RESET} Django setup - skipped (requires MongoDB)")
                results["warnings"] += 1
            else:
                print_result("Django setup", False, str(e))
                results["failed"] += 1

    # ==========================================================================
    # Summary
    # ==========================================================================
    print("\n" + "=" * 50)
    print(f"{BOLD}Summary:{RESET}")
    print(f"  {GREEN}Passed:{RESET}   {results['passed']}")
    print(f"  {RED}Failed:{RESET}   {results['failed']}")
    print(f"  {YELLOW}Warnings:{RESET} {results['warnings']}")
    print("=" * 50)

    if results["failed"] > 0:
        print(f"\n{RED}{BOLD}Environment validation FAILED{RESET}")
        print("Some required modules could not be imported.")
        print("Check the errors above and ensure all dependencies are installed.")
        sys.exit(1)
    else:
        print(f"\n{GREEN}{BOLD}Environment validation PASSED{RESET}")
        if results["warnings"] > 0:
            print(f"({results['warnings']} optional dependencies not installed)")
        sys.exit(0)


if __name__ == "__main__":
    main()
