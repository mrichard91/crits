"""Tests for raw-backed GraphQL TLO queries used by the modern UI."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from crits_api.auth.context import GraphQLContext
from crits_api.auth.user_state import AuthenticatedUser, SourceACL
from crits_api.db.tlo_records import get_tlo_collection
from crits_api.tests.conftest import execute_gql

_TEST_PREFIX = "TestApiRaw"


def _request() -> MagicMock:
    request = MagicMock()
    request.cookies = {}
    return request


def _cleanup_raw_tlo_docs() -> None:
    get_tlo_collection("actors").delete_many({"name": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("backdoors").delete_many({"name": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("campaigns").delete_many({"name": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("certificates").delete_many({"filename": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("domains").delete_many({"domain": {"$regex": f"^{_TEST_PREFIX.lower()}"}})
    get_tlo_collection("emails").delete_many({"subject": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("events").delete_many({"title": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("exploits").delete_many({"name": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("ips").delete_many({"ip": {"$regex": "^203\\.0\\.113\\."}})
    get_tlo_collection("pcaps").delete_many({"filename": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("raw_data").delete_many({"title": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("screenshots").delete_many({"filename": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("signatures").delete_many({"title": {"$regex": f"^{_TEST_PREFIX}"}})
    get_tlo_collection("targets").delete_many(
        {"email_address": {"$regex": f"^{_TEST_PREFIX.lower()}"}}
    )


def _limited_context(tlo_type: str) -> GraphQLContext:
    source_name = f"{_TEST_PREFIX}Source"
    user = AuthenticatedUser(
        id="limited-user",
        username="limited-user",
        is_active=True,
        is_staff=False,
        is_superuser=False,
        organization="TestApiSource",
        acl={tlo_type: {"read": True}},
        source_acls=[SourceACL(name=source_name, read=True, tlp_green=True)],
    )
    return GraphQLContext(request=_request(), response=MagicMock(), user=user, acl=user.acl)


def _insert_actor(*, name: str, source_name: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "name": name,
        "description": "raw actor",
        "aliases": [],
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "identifiers": [],
        "intended_effects": [],
        "motivations": [],
        "sophistications": [],
        "threat_types": [],
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [
            {
                "name": source_name,
                "instances": [
                    {
                        "method": "manual",
                        "reference": "",
                        "analyst": "tester",
                        "date": now,
                        "tlp": "green",
                    }
                ],
            }
        ],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("actors").insert_one(document).inserted_id)


def _insert_campaign(*, name: str, active: str, status: str) -> str:
    now = datetime.now()
    document = {
        "name": name,
        "description": "raw campaign",
        "aliases": [],
        "active": active,
        "analyst": "tester",
        "status": status,
        "tlp": "green",
        "created": now,
        "modified": now,
        "ttps": [],
        "bucket_list": [],
        "sectors": [],
        "source": [],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("campaigns").insert_one(document).inserted_id)


def _insert_target(*, email: str, department: str, division: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "email_address": email,
        "email_count": 1,
        "firstname": "Test",
        "lastname": "Target",
        "title": "Analyst",
        "department": department,
        "division": division,
        "organization_id": "",
        "note": "",
        "description": "raw target",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("targets").insert_one(document).inserted_id)


def _insert_domain(*, domain: str, source_name: str, record_type: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "domain": domain,
        "record_type": record_type,
        "description": "raw domain",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [
            {
                "name": source_name,
                "instances": [
                    {
                        "method": "manual",
                        "reference": "",
                        "analyst": "tester",
                        "date": now,
                        "tlp": "green",
                    }
                ],
            }
        ],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("domains").insert_one(document).inserted_id)


def _insert_ip(*, ip: str, source_name: str, ip_type: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "ip": ip,
        "ip_type": ip_type,
        "description": "raw ip",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [
            {
                "name": source_name,
                "instances": [
                    {
                        "method": "manual",
                        "reference": "",
                        "analyst": "tester",
                        "date": now,
                        "tlp": "green",
                    }
                ],
            }
        ],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("ips").insert_one(document).inserted_id)


def _insert_event(*, title: str, source_name: str, event_type: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "title": title,
        "event_type": event_type,
        "event_id": f"{title}-id",
        "description": "raw event",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [
            {
                "name": source_name,
                "instances": [
                    {
                        "method": "manual",
                        "reference": "",
                        "analyst": "tester",
                        "date": now,
                        "tlp": "green",
                    }
                ],
            }
        ],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("events").insert_one(document).inserted_id)


def _insert_backdoor(*, name: str, source_name: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "name": name,
        "description": "raw backdoor",
        "aliases": [],
        "version": "1.0",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [
            {
                "name": source_name,
                "instances": [
                    {
                        "method": "manual",
                        "reference": "",
                        "analyst": "tester",
                        "date": now,
                        "tlp": "green",
                    }
                ],
            }
        ],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("backdoors").insert_one(document).inserted_id)


def _insert_email(*, subject: str, from_address: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "subject": subject,
        "from_address": from_address,
        "sender": from_address,
        "reply_to": "",
        "to": [f"{_TEST_PREFIX.lower()}@example.com"],
        "cc": [],
        "date": now.isoformat(),
        "isodate": now,
        "message_id": f"<{subject.lower()}@example.com>",
        "originating_ip": "203.0.113.20",
        "x_originating_ip": "",
        "x_mailer": "",
        "helo": "",
        "boundary": "",
        "raw_body": "body",
        "raw_header": "header",
        "description": "raw email",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("emails").insert_one(document).inserted_id)


def _insert_exploit(*, name: str, cve: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "name": name,
        "cve": cve,
        "description": "raw exploit",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("exploits").insert_one(document).inserted_id)


def _insert_signature(*, title: str, data_type: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "title": title,
        "data_type": data_type,
        "data_type_min_version": "",
        "data_type_max_version": "",
        "data_type_dependency": [],
        "data": "rule test { condition: true }",
        "md5": "",
        "link_id": "",
        "version": 1,
        "description": "raw signature",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("signatures").insert_one(document).inserted_id)


def _insert_raw_data(*, title: str, data_type: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "title": title,
        "data_type": data_type,
        "data": "raw data body",
        "md5": "",
        "link_id": "",
        "version": 1,
        "tool": {"name": "parser", "version": "1.0", "details": "raw"},
        "highlights": [],
        "inlines": [],
        "description": "raw raw_data",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("raw_data").insert_one(document).inserted_id)


def _insert_certificate(*, filename: str, md5: str, source_name: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "filename": filename,
        "filetype": "application/x-x509-ca-cert",
        "md5": md5,
        "size": 32,
        "description": "raw certificate",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [
            {
                "name": source_name,
                "instances": [
                    {
                        "method": "manual",
                        "reference": "",
                        "analyst": "tester",
                        "date": now,
                        "tlp": "green",
                    }
                ],
            }
        ],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("certificates").insert_one(document).inserted_id)


def _insert_pcap(*, filename: str, md5: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "filename": filename,
        "contentType": "application/vnd.tcpdump.pcap",
        "md5": md5,
        "length": 64,
        "description": "raw pcap",
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [],
        "relationships": [],
        "actions": [],
        "tickets": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("pcaps").insert_one(document).inserted_id)


def _insert_screenshot(*, filename: str, tag: str, source_name: str, campaign_name: str) -> str:
    now = datetime.now()
    document = {
        "filename": filename,
        "description": "raw screenshot",
        "md5": "",
        "width": 800,
        "height": 600,
        "analyst": "tester",
        "status": "Analyzed",
        "tlp": "green",
        "tags": [tag],
        "created": now,
        "modified": now,
        "campaign": [
            {"name": campaign_name, "analyst": "tester", "confidence": "high", "date": now}
        ],
        "bucket_list": [],
        "sectors": [],
        "source": [
            {
                "name": source_name,
                "instances": [
                    {
                        "method": "manual",
                        "reference": "",
                        "analyst": "tester",
                        "date": now,
                        "tlp": "green",
                    }
                ],
            }
        ],
        "relationships": [],
        "actions": [],
        "schema_version": 1,
    }
    return str(get_tlo_collection("screenshots").insert_one(document).inserted_id)


def test_actor_queries_use_raw_records_with_source_filtering() -> None:
    _cleanup_raw_tlo_docs()
    visible_id = _insert_actor(
        name=f"{_TEST_PREFIX}ActorVisible",
        source_name=f"{_TEST_PREFIX}Source",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    hidden_id = _insert_actor(
        name=f"{_TEST_PREFIX}ActorHidden",
        source_name=f"{_TEST_PREFIX}OtherSource",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        _limited_context("Actor"),
        f"""
        query {{
            visible: actor(id: "{visible_id}") {{ id name }}
            hidden: actor(id: "{hidden_id}") {{ id name }}
            actors(sortBy: "name", sortDir: "asc") {{ name }}
            actorsCount
        }}
        """,
    )

    assert result.errors is None
    assert result.data["visible"]["name"] == f"{_TEST_PREFIX}ActorVisible"
    assert result.data["hidden"] is None
    assert result.data["actors"] == [{"name": f"{_TEST_PREFIX}ActorVisible"}]
    assert result.data["actorsCount"] == 1

    _cleanup_raw_tlo_docs()


def test_campaign_queries_use_raw_records(admin_context: GraphQLContext) -> None:
    _cleanup_raw_tlo_docs()
    matching_id = _insert_campaign(
        name=f"{_TEST_PREFIX}CampaignAlpha",
        active="yes",
        status="Analyzed",
    )
    _insert_campaign(
        name=f"{_TEST_PREFIX}CampaignBeta",
        active="no",
        status="New",
    )

    result = execute_gql(
        admin_context,
        f"""
        query {{
            campaign(id: "{matching_id}") {{ id name active }}
            campaigns(nameContains: "{_TEST_PREFIX}Campaign", active: "yes", sortBy: "name", sortDir: "asc") {{
                name active
            }}
            campaignsCount(nameContains: "{_TEST_PREFIX}Campaign", active: "yes")
            campaignNames
        }}
        """,
    )

    assert result.errors is None
    assert result.data["campaign"]["name"] == f"{_TEST_PREFIX}CampaignAlpha"
    assert result.data["campaigns"] == [{"name": f"{_TEST_PREFIX}CampaignAlpha", "active": "yes"}]
    assert result.data["campaignsCount"] == 1
    assert f"{_TEST_PREFIX}CampaignAlpha" in result.data["campaignNames"]
    assert f"{_TEST_PREFIX}CampaignBeta" in result.data["campaignNames"]

    _cleanup_raw_tlo_docs()


def test_target_queries_use_raw_records(admin_context: GraphQLContext) -> None:
    _cleanup_raw_tlo_docs()
    matching_id = _insert_target(
        email=f"{_TEST_PREFIX.lower()}-alpha@example.com",
        department=f"{_TEST_PREFIX}DeptA",
        division=f"{_TEST_PREFIX}DivisionA",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    _insert_target(
        email=f"{_TEST_PREFIX.lower()}-beta@example.com",
        department=f"{_TEST_PREFIX}DeptB",
        division=f"{_TEST_PREFIX}DivisionB",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        admin_context,
        f"""
        query {{
            target(id: "{matching_id}") {{ id emailAddress department division }}
            targets(department: "{_TEST_PREFIX}DeptA", sortBy: "emailAddress", sortDir: "asc") {{
                emailAddress department division
            }}
            targetsCount(division: "{_TEST_PREFIX}DivisionA")
            targetDepartments
            targetDivisions
        }}
        """,
    )

    assert result.errors is None
    assert result.data["target"]["emailAddress"] == f"{_TEST_PREFIX.lower()}-alpha@example.com"
    assert result.data["targets"] == [
        {
            "emailAddress": f"{_TEST_PREFIX.lower()}-alpha@example.com",
            "department": f"{_TEST_PREFIX}DeptA",
            "division": f"{_TEST_PREFIX}DivisionA",
        }
    ]
    assert result.data["targetsCount"] == 1
    assert f"{_TEST_PREFIX}DeptA" in result.data["targetDepartments"]
    assert f"{_TEST_PREFIX}DeptB" in result.data["targetDepartments"]
    assert f"{_TEST_PREFIX}DivisionA" in result.data["targetDivisions"]
    assert f"{_TEST_PREFIX}DivisionB" in result.data["targetDivisions"]

    _cleanup_raw_tlo_docs()


def test_domain_queries_use_raw_records_with_source_filtering() -> None:
    _cleanup_raw_tlo_docs()
    visible_id = _insert_domain(
        domain=f"{_TEST_PREFIX.lower()}-visible.example.com",
        source_name=f"{_TEST_PREFIX}Source",
        record_type=f"{_TEST_PREFIX}TXT",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    hidden_id = _insert_domain(
        domain=f"{_TEST_PREFIX.lower()}-hidden.example.com",
        source_name=f"{_TEST_PREFIX}OtherSource",
        record_type="TXT",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        _limited_context("Domain"),
        f"""
        query {{
            visible: domain(id: "{visible_id}") {{ id domain recordType }}
            hidden: domain(id: "{hidden_id}") {{ id domain }}
            domains(sortBy: "domain", sortDir: "asc") {{ domain recordType }}
            domainsCount
            domainRecordTypes
        }}
        """,
    )

    assert result.errors is None
    assert result.data["visible"]["domain"] == f"{_TEST_PREFIX.lower()}-visible.example.com"
    assert result.data["visible"]["recordType"] == f"{_TEST_PREFIX}TXT"
    assert result.data["hidden"] is None
    assert result.data["domains"] == [
        {
            "domain": f"{_TEST_PREFIX.lower()}-visible.example.com",
            "recordType": f"{_TEST_PREFIX}TXT",
        }
    ]
    assert result.data["domainsCount"] == 1
    assert "TXT" in result.data["domainRecordTypes"]
    assert f"{_TEST_PREFIX}TXT" in result.data["domainRecordTypes"]

    _cleanup_raw_tlo_docs()


def test_ip_queries_use_raw_records(admin_context: GraphQLContext) -> None:
    _cleanup_raw_tlo_docs()
    matching_id = _insert_ip(
        ip="203.0.113.10",
        source_name=f"{_TEST_PREFIX}Source",
        ip_type=f"{_TEST_PREFIX}CustomIP",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    _insert_ip(
        ip="203.0.113.11",
        source_name=f"{_TEST_PREFIX}Source",
        ip_type="IPv4 Address",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        admin_context,
        f"""
        query {{
            ip(id: "{matching_id}") {{ id ip ipType }}
            ips(ipType: "{_TEST_PREFIX}CustomIP", sortBy: "ip", sortDir: "asc") {{ ip ipType }}
            ipsCount(ipType: "{_TEST_PREFIX}CustomIP")
            ipTypes
        }}
        """,
    )

    assert result.errors is None
    assert result.data["ip"]["ip"] == "203.0.113.10"
    assert result.data["ip"]["ipType"] == f"{_TEST_PREFIX}CustomIP"
    assert result.data["ips"] == [{"ip": "203.0.113.10", "ipType": f"{_TEST_PREFIX}CustomIP"}]
    assert result.data["ipsCount"] == 1
    assert "IPv4 Address" in result.data["ipTypes"]
    assert f"{_TEST_PREFIX}CustomIP" in result.data["ipTypes"]

    _cleanup_raw_tlo_docs()


def test_event_queries_use_raw_records(admin_context: GraphQLContext) -> None:
    _cleanup_raw_tlo_docs()
    matching_id = _insert_event(
        title=f"{_TEST_PREFIX}EventAlpha",
        source_name=f"{_TEST_PREFIX}Source",
        event_type=f"{_TEST_PREFIX}CustomEvent",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    _insert_event(
        title=f"{_TEST_PREFIX}EventBeta",
        source_name=f"{_TEST_PREFIX}Source",
        event_type="Malicious Code",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        admin_context,
        f"""
        query {{
            event(id: "{matching_id}") {{ id title eventType }}
            events(eventType: "{_TEST_PREFIX}CustomEvent", sortBy: "title", sortDir: "asc") {{
                title eventType
            }}
            eventsCount(eventType: "{_TEST_PREFIX}CustomEvent")
            eventTypes
        }}
        """,
    )

    assert result.errors is None
    assert result.data["event"]["title"] == f"{_TEST_PREFIX}EventAlpha"
    assert result.data["event"]["eventType"] == f"{_TEST_PREFIX}CustomEvent"
    assert result.data["events"] == [
        {"title": f"{_TEST_PREFIX}EventAlpha", "eventType": f"{_TEST_PREFIX}CustomEvent"}
    ]
    assert result.data["eventsCount"] == 1
    assert "Malicious Code" in result.data["eventTypes"]
    assert f"{_TEST_PREFIX}CustomEvent" in result.data["eventTypes"]

    _cleanup_raw_tlo_docs()


def test_backdoor_queries_use_raw_records_with_source_filtering() -> None:
    _cleanup_raw_tlo_docs()
    visible_id = _insert_backdoor(
        name=f"{_TEST_PREFIX}BackdoorVisible",
        source_name=f"{_TEST_PREFIX}Source",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    hidden_id = _insert_backdoor(
        name=f"{_TEST_PREFIX}BackdoorHidden",
        source_name=f"{_TEST_PREFIX}OtherSource",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        _limited_context("Backdoor"),
        f"""
        query {{
            visible: backdoor(id: "{visible_id}") {{ id name }}
            hidden: backdoor(id: "{hidden_id}") {{ id name }}
            backdoors(sortBy: "name", sortDir: "asc") {{ name }}
            backdoorsCount
        }}
        """,
    )

    assert result.errors is None
    assert result.data["visible"]["name"] == f"{_TEST_PREFIX}BackdoorVisible"
    assert result.data["hidden"] is None
    assert result.data["backdoors"] == [{"name": f"{_TEST_PREFIX}BackdoorVisible"}]
    assert result.data["backdoorsCount"] == 1

    _cleanup_raw_tlo_docs()


def test_email_queries_use_raw_records(admin_context: GraphQLContext) -> None:
    _cleanup_raw_tlo_docs()
    matching_id = _insert_email(
        subject=f"{_TEST_PREFIX}EmailAlpha",
        from_address="alpha@example.com",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    _insert_email(
        subject=f"{_TEST_PREFIX}EmailBeta",
        from_address="beta@example.com",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        admin_context,
        f"""
        query {{
            email(id: "{matching_id}") {{ id subject fromAddress }}
            emails(subjectContains: "{_TEST_PREFIX}EmailA", fromAddress: "alpha@", sortBy: "subject", sortDir: "asc") {{
                subject fromAddress
            }}
            emailsCount(subjectContains: "{_TEST_PREFIX}EmailA", fromAddress: "alpha@")
        }}
        """,
    )

    assert result.errors is None
    assert result.data["email"]["subject"] == f"{_TEST_PREFIX}EmailAlpha"
    assert result.data["email"]["fromAddress"] == "alpha@example.com"
    assert result.data["emails"] == [
        {"subject": f"{_TEST_PREFIX}EmailAlpha", "fromAddress": "alpha@example.com"}
    ]
    assert result.data["emailsCount"] == 1

    _cleanup_raw_tlo_docs()


def test_exploit_queries_use_raw_records(admin_context: GraphQLContext) -> None:
    _cleanup_raw_tlo_docs()
    matching_id = _insert_exploit(
        name=f"{_TEST_PREFIX}ExploitAlpha",
        cve="CVE-2099-0001",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    _insert_exploit(
        name=f"{_TEST_PREFIX}ExploitBeta",
        cve="CVE-2099-0002",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        admin_context,
        f"""
        query {{
            exploit(id: "{matching_id}") {{ id name cve }}
            exploits(nameContains: "{_TEST_PREFIX}ExploitA", cve: "0001", sortBy: "name", sortDir: "asc") {{
                name cve
            }}
            exploitsCount(nameContains: "{_TEST_PREFIX}ExploitA", cve: "0001")
        }}
        """,
    )

    assert result.errors is None
    assert result.data["exploit"]["name"] == f"{_TEST_PREFIX}ExploitAlpha"
    assert result.data["exploit"]["cve"] == "CVE-2099-0001"
    assert result.data["exploits"] == [
        {"name": f"{_TEST_PREFIX}ExploitAlpha", "cve": "CVE-2099-0001"}
    ]
    assert result.data["exploitsCount"] == 1

    _cleanup_raw_tlo_docs()


def test_signature_queries_use_raw_records(admin_context: GraphQLContext) -> None:
    _cleanup_raw_tlo_docs()
    matching_id = _insert_signature(
        title=f"{_TEST_PREFIX}SignatureAlpha",
        data_type=f"{_TEST_PREFIX}YARA",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    _insert_signature(
        title=f"{_TEST_PREFIX}SignatureBeta",
        data_type="YARA",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        admin_context,
        f"""
        query {{
            signature(id: "{matching_id}") {{ id title dataType }}
            signatures(titleContains: "{_TEST_PREFIX}SignatureA", dataType: "{_TEST_PREFIX}YARA", sortBy: "title", sortDir: "asc") {{
                title dataType
            }}
            signaturesCount(titleContains: "{_TEST_PREFIX}SignatureA", dataType: "{_TEST_PREFIX}YARA")
            signatureDataTypes
        }}
        """,
    )

    assert result.errors is None
    assert result.data["signature"]["title"] == f"{_TEST_PREFIX}SignatureAlpha"
    assert result.data["signature"]["dataType"] == f"{_TEST_PREFIX}YARA"
    assert result.data["signatures"] == [
        {"title": f"{_TEST_PREFIX}SignatureAlpha", "dataType": f"{_TEST_PREFIX}YARA"}
    ]
    assert result.data["signaturesCount"] == 1
    assert "YARA" in result.data["signatureDataTypes"]
    assert f"{_TEST_PREFIX}YARA" in result.data["signatureDataTypes"]

    _cleanup_raw_tlo_docs()


def test_raw_data_queries_use_raw_records(admin_context: GraphQLContext) -> None:
    _cleanup_raw_tlo_docs()
    matching_id = _insert_raw_data(
        title=f"{_TEST_PREFIX}RawDataAlpha",
        data_type=f"{_TEST_PREFIX}Log",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    _insert_raw_data(
        title=f"{_TEST_PREFIX}RawDataBeta",
        data_type="Log",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        admin_context,
        f"""
        query {{
            rawData(id: "{matching_id}") {{ id title dataType }}
            rawDataList(titleContains: "{_TEST_PREFIX}RawDataA", dataType: "{_TEST_PREFIX}Log", sortBy: "title", sortDir: "asc") {{
                title dataType
            }}
            rawDataCount(titleContains: "{_TEST_PREFIX}RawDataA", dataType: "{_TEST_PREFIX}Log")
        }}
        """,
    )

    assert result.errors is None
    assert result.data["rawData"]["title"] == f"{_TEST_PREFIX}RawDataAlpha"
    assert result.data["rawData"]["dataType"] == f"{_TEST_PREFIX}Log"
    assert result.data["rawDataList"] == [
        {"title": f"{_TEST_PREFIX}RawDataAlpha", "dataType": f"{_TEST_PREFIX}Log"}
    ]
    assert result.data["rawDataCount"] == 1

    _cleanup_raw_tlo_docs()


def test_certificate_queries_use_raw_records_with_source_filtering() -> None:
    _cleanup_raw_tlo_docs()
    visible_id = _insert_certificate(
        filename=f"{_TEST_PREFIX}CertVisible.crt",
        md5="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        source_name=f"{_TEST_PREFIX}Source",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    hidden_id = _insert_certificate(
        filename=f"{_TEST_PREFIX}CertHidden.crt",
        md5="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        source_name=f"{_TEST_PREFIX}OtherSource",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        _limited_context("Certificate"),
        f"""
        query {{
            visible: certificate(id: "{visible_id}") {{ id filename md5 }}
            hidden: certificate(id: "{hidden_id}") {{ id filename }}
            certificates(filenameContains: "{_TEST_PREFIX}Cert", sortBy: "filename", sortDir: "asc") {{
                filename md5
            }}
            certificatesCount(filenameContains: "{_TEST_PREFIX}Cert")
        }}
        """,
    )

    assert result.errors is None
    assert result.data["visible"]["filename"] == f"{_TEST_PREFIX}CertVisible.crt"
    assert result.data["hidden"] is None
    assert result.data["certificates"] == [
        {
            "filename": f"{_TEST_PREFIX}CertVisible.crt",
            "md5": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        }
    ]
    assert result.data["certificatesCount"] == 1

    _cleanup_raw_tlo_docs()


def test_pcap_queries_use_raw_records(admin_context: GraphQLContext) -> None:
    _cleanup_raw_tlo_docs()
    matching_id = _insert_pcap(
        filename=f"{_TEST_PREFIX}CaptureAlpha.pcap",
        md5="cccccccccccccccccccccccccccccccc",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    _insert_pcap(
        filename=f"{_TEST_PREFIX}CaptureBeta.pcap",
        md5="dddddddddddddddddddddddddddddddd",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        admin_context,
        f"""
        query {{
            pcap(id: "{matching_id}") {{ id filename md5 }}
            pcaps(filenameContains: "{_TEST_PREFIX}CaptureA", md5: "cccccccccccccccccccccccccccccccc", sortBy: "filename", sortDir: "asc") {{
                filename md5
            }}
            pcapsCount(filenameContains: "{_TEST_PREFIX}CaptureA", md5: "cccccccccccccccccccccccccccccccc")
        }}
        """,
    )

    assert result.errors is None
    assert result.data["pcap"]["filename"] == f"{_TEST_PREFIX}CaptureAlpha.pcap"
    assert result.data["pcap"]["md5"] == "cccccccccccccccccccccccccccccccc"
    assert result.data["pcaps"] == [
        {
            "filename": f"{_TEST_PREFIX}CaptureAlpha.pcap",
            "md5": "cccccccccccccccccccccccccccccccc",
        }
    ]
    assert result.data["pcapsCount"] == 1

    _cleanup_raw_tlo_docs()


def test_screenshot_queries_use_raw_records_with_source_filtering() -> None:
    _cleanup_raw_tlo_docs()
    visible_id = _insert_screenshot(
        filename=f"{_TEST_PREFIX}ShotVisible.png",
        tag=f"{_TEST_PREFIX}Tag",
        source_name=f"{_TEST_PREFIX}Source",
        campaign_name=f"{_TEST_PREFIX}CampaignOne",
    )
    hidden_id = _insert_screenshot(
        filename=f"{_TEST_PREFIX}ShotHidden.png",
        tag=f"{_TEST_PREFIX}Tag",
        source_name=f"{_TEST_PREFIX}OtherSource",
        campaign_name=f"{_TEST_PREFIX}CampaignTwo",
    )

    result = execute_gql(
        _limited_context("Screenshot"),
        f"""
        query {{
            visible: screenshot(id: "{visible_id}") {{ id filename tags }}
            hidden: screenshot(id: "{hidden_id}") {{ id filename }}
            screenshots(filenameContains: "{_TEST_PREFIX}Shot", tag: "{_TEST_PREFIX}Tag", sortBy: "filename", sortDir: "asc") {{
                filename tags
            }}
            screenshotsCount(filenameContains: "{_TEST_PREFIX}Shot", tag: "{_TEST_PREFIX}Tag")
        }}
        """,
    )

    assert result.errors is None
    assert result.data["visible"]["filename"] == f"{_TEST_PREFIX}ShotVisible.png"
    assert result.data["hidden"] is None
    assert result.data["screenshots"] == [
        {"filename": f"{_TEST_PREFIX}ShotVisible.png", "tags": [f"{_TEST_PREFIX}Tag"]}
    ]
    assert result.data["screenshotsCount"] == 1

    _cleanup_raw_tlo_docs()
