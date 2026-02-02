#!/usr/bin/env python
"""
Bootstrap script to create test data for CRITs GraphQL API development.

Creates sample indicators (IPs and domains) for testing queries.

Usage:
    docker compose exec web uv run python scripts/bootstrap_test_data.py

Or run directly:
    docker compose exec -T web uv run python < scripts/bootstrap_test_data.py
"""

import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crits.settings')

import django
django.setup()

from datetime import datetime
from crits.indicators.indicator import Indicator
from crits.core.crits_mongoengine import EmbeddedSource, EmbeddedCampaign
from crits.core.user import CRITsUser


def create_source_with_instance(source_name: str, analyst: str, tlp: str = "green"):
    """
    Create a properly structured EmbeddedSource with instance.

    The source must have instances with TLP for CRITs access control to work.
    """
    SourceInstance = EmbeddedSource.SourceInstance

    source = EmbeddedSource()
    source.name = source_name

    instance = SourceInstance()
    instance.analyst = analyst
    instance.date = datetime.now()
    instance.method = "Bootstrap script"
    instance.reference = ""
    instance.tlp = tlp

    source.instances = [instance]
    return source


def create_test_indicators():
    """Create test indicators for development."""

    # Use source that admin has access to
    source_name = "test"
    analyst = "admin"

    # Test IP indicators
    test_ips = [
        ("192.168.1.100", "Suspicious internal host", "green"),
        ("10.0.0.50", "Potential C2 server", "green"),
        ("203.0.113.42", "Known malicious IP", "amber"),
        ("198.51.100.23", "Phishing campaign source", "amber"),
        ("172.16.0.99", "Lateral movement indicator", "green"),
    ]

    # Test domain indicators
    test_domains = [
        ("malware-c2.evil.com", "Command and control domain", "red"),
        ("phishing-login.badsite.net", "Credential harvesting site", "amber"),
        ("data-exfil.suspicious.org", "Data exfiltration endpoint", "amber"),
        ("dropper.malicious.io", "Malware distribution domain", "red"),
        ("tracker.adware.biz", "Adware tracking domain", "green"),
    ]

    created_count = 0
    skipped_count = 0

    print("Creating test indicators...")
    print("-" * 50)

    # Create IP indicators
    for ip, description, tlp in test_ips:
        # Check if already exists
        existing = Indicator.objects(value=ip).first()
        if existing:
            print(f"  SKIP: IP {ip} already exists")
            skipped_count += 1
            continue

        indicator = Indicator()
        indicator.value = ip
        indicator.lower = ip.lower()
        indicator.ind_type = "Address - ipv4-addr"
        indicator.description = description
        indicator.analyst = analyst
        indicator.status = "Analyzed"
        indicator.tlp = tlp

        # Add source with instance (required for access control)
        indicator.source = [create_source_with_instance(source_name, analyst, tlp)]

        # Add campaign
        campaign = EmbeddedCampaign()
        campaign.name = "Test Campaign"
        campaign.confidence = "medium"
        campaign.analyst = analyst
        indicator.campaign = [campaign]

        try:
            indicator.save()
            print(f"  CREATE: IP {ip} (TLP: {tlp})")
            created_count += 1
        except Exception as e:
            print(f"  ERROR: IP {ip} - {e}")

    # Create domain indicators
    for domain, description, tlp in test_domains:
        # Check if already exists
        existing = Indicator.objects(value=domain).first()
        if existing:
            print(f"  SKIP: Domain {domain} already exists")
            skipped_count += 1
            continue

        indicator = Indicator()
        indicator.value = domain
        indicator.lower = domain.lower()
        indicator.ind_type = "URI - Domain Name"
        indicator.description = description
        indicator.analyst = analyst
        indicator.status = "New"
        indicator.tlp = tlp

        # Add source with instance (required for access control)
        indicator.source = [create_source_with_instance(source_name, analyst, tlp)]

        try:
            indicator.save()
            print(f"  CREATE: Domain {domain} (TLP: {tlp})")
            created_count += 1
        except Exception as e:
            print(f"  ERROR: Domain {domain} - {e}")

    print("-" * 50)
    print(f"Done! Created: {created_count}, Skipped: {skipped_count}")
    print(f"Total indicators in database: {Indicator.objects.count()}")


def clear_test_indicators():
    """Remove test indicators (optional cleanup)."""
    test_values = [
        "192.168.1.100", "10.0.0.50", "203.0.113.42", "198.51.100.23", "172.16.0.99",
        "malware-c2.evil.com", "phishing-login.badsite.net", "data-exfil.suspicious.org",
        "dropper.malicious.io", "tracker.adware.biz"
    ]

    deleted = 0
    for value in test_values:
        result = Indicator.objects(value=value).delete()
        if result:
            deleted += result
            print(f"  Deleted: {value}")

    print(f"\nDeleted {deleted} test indicators")
    print(f"Remaining indicators: {Indicator.objects.count()}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_test_indicators()
    else:
        create_test_indicators()
