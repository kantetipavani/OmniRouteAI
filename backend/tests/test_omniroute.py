"""
Comprehensive Unit and Integration Test Suite for OmniRoute.
"""
import pytest

from app.services.generator import SyntheticDataGenerator
from app.services.router import router_service
from app.services.validator import data_validator
from app.database import get_collection
from app.api.endpoints import (
    get_dashboard_stats, list_tickets, get_ticket_detail,
    route_case, list_agents, list_queues, list_anomalies,
    get_data_dictionary, execute_ticket_action
)
from app.models.schemas import RoutingRequest, ActionRequest

@pytest.fixture(autouse=True, scope="session")
def seed_test_database():
    gen = SyntheticDataGenerator(seed=20261022)
    data = gen.generate_all("starter")
    collections_to_load = [
        ("customers", data["customers"]),
        ("channels", data["channels"]),
        ("languages", data["languages"]),
        ("skills", data["skills"]),
        ("queues", data["queues"]),
        ("intents", data["intents"]),
        ("priority_rules", data["priority_rules"]),
        ("agents", data["agents"]),
        ("tickets", data["tickets"]),
        ("messages", data["messages"]),
        ("assignment_events", data["assignment_events"]),
        ("sla_events", data["sla_events"]),
        ("resolutions", data["resolutions"]),
        ("ground_truth", data["ground_truth"])
    ]
    for col_name, records in collections_to_load:
        col = get_collection(col_name)
        col.delete_many({})
        if records:
            col.insert_many([dict(r) for r in records])

def test_deterministic_reproducibility():
    """Step 10: Compare checksums and row counts between identical seed runs."""
    gen1 = SyntheticDataGenerator(seed=20261022)
    run1 = gen1.generate_all("starter")

    gen2 = SyntheticDataGenerator(seed=20261022)
    run2 = gen2.generate_all("starter")

    assert run1["manifest"]["dataset_sha256"] == run2["manifest"]["dataset_sha256"], "Checksums must match for identical seeds"
    assert run1["manifest"]["counts"] == run2["manifest"]["counts"], "Row counts must match exactly"

def test_edge_case_injection():
    """Verify all 5 required edge cases are present in ground truth."""
    gen = SyntheticDataGenerator(seed=20261022)
    data = gen.generate_all("starter")
    anomalies = data["ground_truth"]
    issue_types = {a["issue_type"] for a in anomalies}
    
    expected_issues = {
        "CAPACITY_EXCEEDED",
        "CALENDAR_IGNORED",
        "HISTORY_LOST",
        "TRANSFER_LOOP",
        "SAFETY_OVERRIDE_VIOLATION"
    }
    assert expected_issues.issubset(issue_types), f"Missing edge cases in {issue_types}"

def test_intelligent_routing_engine():
    """Verify live routing selects eligible agent, logs assignment event, and computes SLA."""
    res = router_service.route_ticket(
        channel_id="CH-CHAT",
        customer_id="CUST-000001",
        intent_id="INT-007",  # Security breach
        language_code="en",
        initial_message="URGENT: Suspicious unauthorized login attempt from foreign IP."
    )

    ticket = res["ticket"]
    assignment = res["assignment_event"]
    sla = res["sla_event"]
    trace = res["routing_reasoning"]["trace"]

    assert ticket["ticket_id"].startswith("TKT-2026-")
    assert ticket["urgency"] == "CRITICAL"
    assert assignment["to_agent_id"].startswith("AGT-")
    assert sla["target_frt_minutes"] <= 5
    assert len(trace) >= 4

def test_validation_suite():
    """Verify validation suite passes on generated dataset."""
    report = data_validator.run_full_validation()
    assert report["score"] >= 80.0
    assert report["passed_checks"] >= 5

def test_endpoint_dashboard_stats():
    """Verify get_dashboard_stats returns operational metrics."""
    stats = get_dashboard_stats()
    assert stats["total_tickets"] >= 1000
    assert stats["total_agents"] >= 25
    assert "sla_compliance_rate" in stats
    assert "channel_distribution" in stats

def test_endpoint_tickets_and_detail():
    """Verify list_tickets and get_ticket_detail."""
    res = list_tickets(limit=5)
    assert len(res["tickets"]) == 5
    first_id = res["tickets"][0]["ticket_id"]

    detail = get_ticket_detail(first_id)
    assert detail["ticket"]["ticket_id"] == first_id
    assert "customer" in detail
    assert "messages" in detail
    assert "assignment_history" in detail

def test_endpoint_route_case():
    """Verify route_case endpoint simulates case routing with reasoning trace."""
    req = RoutingRequest(
        channel_id="CH-EMAIL",
        customer_id="CUST-000002",
        intent_id="INT-001",
        language_code="en",
        initial_message="Need clarification on invoice discrepancy for billing."
    )
    data = route_case(req)
    assert data["ticket"]["ticket_id"].startswith("TKT-2026-")
    assert data["assignment_event"]["to_agent_id"].startswith("AGT-")
    assert "routing_reasoning" in data

def test_endpoint_ticket_action():
    """Verify action endpoint handles RESOLVE action."""
    action_res = execute_ticket_action(
        ticket_id="TKT-2026-000001",
        action="RESOLVE",
        req=ActionRequest(notes="Resolved via unit test", csat_score=5)
    )
    assert action_res["status"] == "SUCCESS"
    assert action_res["action"] == "RESOLVE"

def test_endpoint_anomalies_and_dictionary():
    """Verify list_anomalies, list_agents, list_queues, and get_data_dictionary."""
    anomalies = list_anomalies()
    assert len(anomalies) > 0
    agents = list_agents()
    assert len(agents) >= 25
    queues = list_queues()
    assert len(queues) >= 5
    d = get_data_dictionary()
    assert "Ticket" in d
    assert "Customer" in d
    assert "Channel" in d
    assert "AssignmentEvent" in d
