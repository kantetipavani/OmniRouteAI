"""
REST API Endpoints for OmniRoute.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from app.database import get_collection
from app.models.schemas import (
    RoutingRequest, RoutingDecisionResponse, TicketDetailResponse, ActionRequest,
    DatasetGenerationConfig
)
from app.models.dictionary import DATA_DICTIONARY
from app.services.router import router_service
from app.services.validator import data_validator
from app.services.generator import SyntheticDataGenerator

api_router = APIRouter(prefix="/api")

@api_router.get("/dashboard/stats")
def get_dashboard_stats():
    db_tickets = get_collection("tickets")
    db_agents = get_collection("agents")
    db_sla = get_collection("sla_events")
    db_resolutions = get_collection("resolutions")
    db_anomalies = get_collection("ground_truth")

    total_tickets = db_tickets.count_documents({})
    total_agents = db_agents.count_documents({})
    total_anomalies = db_anomalies.count_documents({})

    # SLA stats
    met_sla = db_sla.count_documents({"frt_status": "MET"})
    total_sla = db_sla.count_documents({})
    sla_compliance_rate = round((met_sla / total_sla * 100), 1) if total_sla > 0 else 100.0

    # Backlog count
    backlog_count = db_tickets.count_documents({"status": {"$in": ["NEW", "ASSIGNED", "IN_PROGRESS", "TRANSFERRED", "REOPENED"]}})

    # Average CSAT
    resolutions = list(db_resolutions.find({"customer_satisfaction_score": {"$ne": None}}))
    avg_csat = round(sum(r["customer_satisfaction_score"] for r in resolutions) / len(resolutions), 2) if resolutions else 4.5

    # Channel counts
    channels = ["CH-EMAIL", "CH-CHAT", "CH-PHONE"]
    channel_distribution = {
        c: db_tickets.count_documents({"channel_id": c}) for c in channels
    }

    # Urgency breakdown
    urgency_counts = {
        u: db_tickets.count_documents({"urgency": u}) for u in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    }

    # Agent capacity utilization
    agents = list(db_agents.find({}))
    total_capacity = sum(a.get("max_concurrent_capacity", 5.0) for a in agents)
    total_current_load = sum(a.get("current_load", 0.0) for a in agents)
    capacity_utilization = round((total_current_load / total_capacity * 100), 1) if total_capacity > 0 else 0.0

    return {
        "total_tickets": total_tickets,
        "total_agents": total_agents,
        "backlog_count": backlog_count,
        "sla_compliance_rate": sla_compliance_rate,
        "average_csat": avg_csat,
        "total_anomalies": total_anomalies,
        "capacity_utilization_pct": capacity_utilization,
        "channel_distribution": channel_distribution,
        "urgency_counts": urgency_counts
    }

@api_router.get("/tickets")
def list_tickets(
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    channel_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    anomaly_only: bool = False,
    limit: int = 50,
    offset: int = 0
):
    query = {}
    if status:
        query["status"] = status.strip().upper()
    if urgency:
        query["urgency"] = urgency.strip().upper()
    if channel_id:
        c_norm = channel_id.strip().upper()
        if c_norm in ["EMAIL", "CH-EMAIL"]:
            query["channel_id"] = "CH-EMAIL"
        elif c_norm in ["CHAT", "CH-CHAT"]:
            query["channel_id"] = "CH-CHAT"
        elif c_norm in ["PHONE", "CH-PHONE"]:
            query["channel_id"] = "CH-PHONE"
        else:
            query["channel_id"] = channel_id.strip()
    if agent_id:
        query["assigned_agent_id"] = agent_id.strip()
    if anomaly_only:
        query["anomaly_flag"] = {"$ne": None}

    db_tickets = get_collection("tickets")
    total = db_tickets.count_documents(query)
    raw_tickets = list(db_tickets.find(query).skip(offset).limit(limit))

    # Enrich with SLA event summary for each ticket
    db_sla = get_collection("sla_events")
    ticket_ids = [t.get("ticket_id") for t in raw_tickets if t.get("ticket_id")]
    sla_map = {}
    if ticket_ids:
        for s in db_sla.find({"ticket_id": {"$in": ticket_ids}}):
            sla_map[s["ticket_id"]] = {
                "sla_id": s.get("sla_id"),
                "calendar_type": s.get("calendar_type"),
                "frt_status": s.get("frt_status"),
                "ttr_status": s.get("ttr_status"),
                "frt_deadline": s.get("frt_deadline"),
                "ttr_deadline": s.get("ttr_deadline"),
                "is_escalated": s.get("is_escalated", False)
            }

    for t in raw_tickets:
        t.pop("_id", None)
        t["sla"] = sla_map.get(t.get("ticket_id"))

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "tickets": raw_tickets
    }

@api_router.get("/tickets/{ticket_id}")
def get_ticket_detail(ticket_id: str):
    db_tickets = get_collection("tickets")
    db_customers = get_collection("customers")
    db_agents = get_collection("agents")
    db_channels = get_collection("channels")
    db_intents = get_collection("intents")
    db_messages = get_collection("messages")
    db_assignments = get_collection("assignment_events")
    db_sla = get_collection("sla_events")
    db_resolutions = get_collection("resolutions")
    db_ground_truth = get_collection("ground_truth")

    ticket = db_tickets.find_one({"ticket_id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    ticket.pop("_id", None)
    customer = db_customers.find_one({"customer_id": ticket.get("customer_id")})
    if customer: customer.pop("_id", None)

    agent = db_agents.find_one({"agent_id": ticket.get("assigned_agent_id")})
    if agent: agent.pop("_id", None)

    channel = db_channels.find_one({"channel_id": ticket.get("channel_id")})
    if channel: channel.pop("_id", None)

    intent = db_intents.find_one({"intent_id": ticket.get("intent_id")})
    if intent: intent.pop("_id", None)

    messages = list(db_messages.find({"ticket_id": ticket_id}).sort("timestamp", 1))
    for m in messages: m.pop("_id", None)

    assignments = list(db_assignments.find({"ticket_id": ticket_id}).sort("timestamp", 1))
    for a in assignments: a.pop("_id", None)

    sla_event = db_sla.find_one({"ticket_id": ticket_id})
    if sla_event: sla_event.pop("_id", None)

    resolution = db_resolutions.find_one({"ticket_id": ticket_id})
    if resolution: resolution.pop("_id", None)

    anomaly = db_ground_truth.find_one({"ticket_id": ticket_id})
    if anomaly: anomaly.pop("_id", None)

    return {
        "ticket": ticket,
        "customer": customer,
        "agent": agent,
        "channel": channel,
        "intent": intent,
        "messages": messages,
        "assignment_history": assignments,
        "sla_event": sla_event,
        "resolution": resolution,
        "anomaly": anomaly
    }

@api_router.post("/tickets/route")
def route_case(req: RoutingRequest):
    result = router_service.route_ticket(
        channel_id=req.channel_id,
        customer_id=req.customer_id,
        intent_id=req.intent_id,
        language_code=req.language_code,
        initial_message=req.initial_message,
        urgency_override=req.urgency_override
    )
    return result

@api_router.post("/tickets/{ticket_id}/action")
def execute_ticket_action(ticket_id: str, action: str = Query(..., pattern="^(TRANSFER|ESCALATE|RESOLVE|REOPEN)$"), req: ActionRequest = None):
    db_tickets = get_collection("tickets")
    db_assignments = get_collection("assignment_events")
    db_resolutions = get_collection("resolutions")
    db_messages = get_collection("messages")
    db_agents = get_collection("agents")

    ticket = db_tickets.find_one({"ticket_id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    now = datetime.now(timezone.utc).isoformat()
    req = req or ActionRequest()

    if action == "TRANSFER":
        target_agent = req.target_agent_id or "AGT-000002"
        target_queue = req.target_queue_id or "QUE-TIER2"
        new_count = ticket.get("transfer_count", 0) + 1
        
        db_tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"assigned_agent_id": target_agent, "queue_id": target_queue, "status": "TRANSFERRED", "transfer_count": new_count}}
        )
        asn_id = f"ASN-{ticket_id}-{len(list(db_assignments.find({'ticket_id': ticket_id})))+1:03d}"
        db_assignments.insert_one({
            "assignment_id": asn_id,
            "ticket_id": ticket_id,
            "event_type": "TRANSFERRED",
            "from_agent_id": ticket.get("assigned_agent_id"),
            "to_agent_id": target_agent,
            "from_queue_id": ticket.get("queue_id"),
            "to_queue_id": target_queue,
            "reason": req.reason or "Specialist transfer",
            "agent_load_at_assignment": 2.0,
            "agent_max_capacity": 5.0,
            "matched_skills": ["SKL-TECH-CORE"],
            "matched_language": True,
            "timestamp": now
        })
        return {"status": "SUCCESS", "action": "TRANSFER", "ticket_id": ticket_id, "transferred_to": target_agent}

    elif action == "ESCALATE":
        new_level = ticket.get("escalation_level", 0) + 1
        db_tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status": "ESCALATED", "escalation_level": new_level, "queue_id": "QUE-EXEC"}}
        )
        asn_id = f"ASN-{ticket_id}-{len(list(db_assignments.find({'ticket_id': ticket_id})))+1:03d}"
        db_assignments.insert_one({
            "assignment_id": asn_id,
            "ticket_id": ticket_id,
            "event_type": "ESCALATED",
            "from_agent_id": ticket.get("assigned_agent_id"),
            "to_agent_id": "AGT-000001",
            "from_queue_id": ticket.get("queue_id"),
            "to_queue_id": "QUE-EXEC",
            "reason": req.reason or "Manager escalation",
            "agent_load_at_assignment": 1.0,
            "agent_max_capacity": 4.0,
            "matched_skills": ["SKL-SECURITY"],
            "matched_language": True,
            "timestamp": now
        })
        return {"status": "SUCCESS", "action": "ESCALATE", "ticket_id": ticket_id, "escalation_level": new_level}

    elif action == "RESOLVE":
        db_tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status": "RESOLVED", "resolved_at": now}}
        )
        db_resolutions.insert_one({
            "resolution_id": f"RES-{ticket_id}",
            "ticket_id": ticket_id,
            "resolved_by_agent_id": ticket.get("assigned_agent_id") or "AGT-000001",
            "resolution_type": "FIRST_CONTACT_RESOLUTION",
            "root_cause_category": "USER_GUIDANCE",
            "notes": req.notes or "Resolved by agent intervention.",
            "customer_satisfaction_score": req.csat_score or 5,
            "csat_feedback": req.csat_feedback or "Prompt resolution.",
            "resolved_at": now
        })
        return {"status": "SUCCESS", "action": "RESOLVE", "ticket_id": ticket_id}

    elif action == "REOPEN":
        new_reopen_count = ticket.get("reopen_count", 0) + 1
        db_tickets.update_one(
            {"ticket_id": ticket_id},
            {"$set": {"status": "REOPENED", "is_reopened": True, "reopen_count": new_reopen_count}}
        )
        db_messages.insert_one({
            "message_id": f"MSG-{ticket_id}-{len(list(db_messages.find({'ticket_id': ticket_id})))+1:03d}",
            "ticket_id": ticket_id,
            "sender_type": "CUSTOMER",
            "sender_id": ticket.get("customer_id"),
            "channel_id": ticket.get("channel_id"),
            "content": "Reopening case: The issue has recurred.",
            "timestamp": now,
            "is_internal_note": False
        })
        return {"status": "SUCCESS", "action": "REOPEN", "ticket_id": ticket_id, "reopen_count": new_reopen_count}

@api_router.get("/agents")
def list_agents():
    db_agents = get_collection("agents")
    agents = list(db_agents.find({}))
    for a in agents:
        a.pop("_id", None)
    return agents

@api_router.get("/queues")
def list_queues():
    db_queues = get_collection("queues")
    db_tickets = get_collection("tickets")
    queues = list(db_queues.find({}))
    for q in queues:
        q.pop("_id", None)
        q["active_tickets"] = db_tickets.count_documents({"queue_id": q["queue_id"], "status": {"$ne": "RESOLVED"}})
    return queues

@api_router.get("/anomalies")
def list_anomalies(issue_type: Optional[str] = None):
    db_anomalies = get_collection("ground_truth")
    query = {}
    if issue_type:
        query["issue_type"] = issue_type
    anomalies = list(db_anomalies.find(query))
    for a in anomalies:
        a.pop("_id", None)
    return anomalies

@api_router.get("/validation/report")
def run_validation():
    return data_validator.run_full_validation()

@api_router.get("/validation/reproducibility")
def run_reproducibility(seed: int = 20261022):
    return data_validator.verify_reproducibility(seed=seed)

@api_router.get("/dictionary")
def get_data_dictionary():
    return DATA_DICTIONARY

@api_router.post("/generator/run")
def trigger_generator(config: DatasetGenerationConfig):
    gen = SyntheticDataGenerator(seed=config.seed)
    data = gen.generate_all(scale=config.scale)
    gen.export_to_disk(data, output_dir="backend/data")

    # Load generated data into MongoDB collections
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
            # Insert a copy without mutating the original dictionary
            clean_records = [dict(r) for r in records]
            col.insert_many(clean_records)

    return {
        "status": "SUCCESS",
        "scale": config.scale,
        "seed": config.seed,
        "manifest": data["manifest"]
    }
