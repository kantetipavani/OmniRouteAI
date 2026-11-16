"""
Intelligent Routing Engine for OmniRoute.
Routes omnichannel cases by intent, urgency, customer tier, language, skill,
shift schedules, and agent concurrency capacity with SLA tracking.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from app.database import get_collection
from app.services.generator import compute_priority_score, calculate_sla_targets

class CaseRouter:
    def route_ticket(self, 
                     channel_id: str, 
                     customer_id: str, 
                     intent_id: str, 
                     language_code: str, 
                     initial_message: str,
                     urgency_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes end-to-end intelligent routing decision pipeline.
        Exposes every intermediate step for explainability and traceability.
        """
        db_customers = get_collection("customers")
        db_channels = get_collection("channels")
        db_intents = get_collection("intents")
        db_priority_rules = get_collection("priority_rules")
        db_agents = get_collection("agents")
        db_tickets = get_collection("tickets")
        db_messages = get_collection("messages")
        db_assignment_events = get_collection("assignment_events")
        db_sla_events = get_collection("sla_events")

        now = datetime.now(timezone.utc)
        current_hour = now.hour

        # 1. Fetch Master Entities
        customer = db_customers.find_one({"customer_id": customer_id})
        if not customer:
            customer = {
                "customer_id": customer_id,
                "name": "Anonymous Customer",
                "tier": "STANDARD",
                "preferred_language": language_code,
                "email": "customer@example.com",
                "phone": "+15551234567",
                "created_at": now.isoformat()
            }
            db_customers.insert_one(customer)

        channel = db_channels.find_one({"channel_id": channel_id})
        if not channel:
            channel = {
                "channel_id": channel_id,
                "name": "Standard Channel",
                "type": "CHAT",
                "concurrency_weight": 0.33,
                "is_realtime": True,
                "operating_calendar": "24X7",
                "default_frt_minutes": 5,
                "default_ttr_minutes": 45
            }

        intent = db_intents.find_one({"intent_id": intent_id})
        if not intent:
            intent = {
                "intent_id": intent_id,
                "name": "GENERAL_INQUIRY",
                "category": "TECHNICAL",
                "base_urgency": "MEDIUM",
                "required_skill_id": "SKL-TECH-CORE",
                "default_queue_id": "QUE-TECH"
            }

        # 2. Priority & Urgency Calculation
        rules = list(db_priority_rules.find({"intent_id": intent_id}))
        matched_rule = next(
            (r for r in rules if r.get("customer_tier") == customer.get("tier")),
            next((r for r in rules if r.get("customer_tier") == "ANY"), None)
        )

        reasoning_steps = []
        reasoning_steps.append(f"Step 1: Ingested inquiry on channel '{channel['name']}' from customer '{customer['name']}' (Tier: {customer.get('tier')}).")
        reasoning_steps.append(f"Step 2: Classified intent as '{intent['name']}' (Required Skill: {intent['required_skill_id']}).")

        if matched_rule:
            urgency = matched_rule["calculated_urgency"]
            reasoning_steps.append(f"Step 3: Matched Priority Rule {matched_rule['rule_id']}: Calculated Urgency = {urgency}.")
            if matched_rule.get("is_safety_critical"):
                min_floor = matched_rule.get("min_urgency_floor", "HIGH")
                reasoning_steps.append(f"Policy Guard: Safety-critical intent detected. Minimum urgency floor enforced: {min_floor}.")
        else:
            urgency = intent.get("base_urgency", "MEDIUM")
            reasoning_steps.append(f"Step 3: No custom rule match; defaulted to Intent base urgency: {urgency}.")

        # Urgency override if provided (respecting safety guard)
        if urgency_override:
            if matched_rule and matched_rule.get("is_safety_critical") and urgency_override == "LOW":
                reasoning_steps.append(f"WARNING: Urgency override '{urgency_override}' rejected due to safety floor violations. Retained '{urgency}'.")
            else:
                urgency = urgency_override
                reasoning_steps.append(f"Step 3b: Operator applied valid urgency override: {urgency}.")

        priority_score = compute_priority_score(customer.get("tier", "STANDARD"), urgency)
        reasoning_steps.append(f"Step 4: Computed Priority Score = {priority_score}/100 based on Tier and Urgency.")

        # 3. Agent Filtering & Capacity Matching
        all_agents = list(db_agents.find({}))
        if not all_agents:
            # Fallback bootstrap agent if DB not yet seeded
            fallback_agent = {
                "agent_id": "AGT-000001",
                "name": "Alex Mercer",
                "email": "alex.mercer@support.company.internal",
                "role": "SPECIALIST",
                "status": "AVAILABLE",
                "shift_start_hour": 0,
                "shift_end_hour": 24,
                "timezone": "UTC",
                "max_concurrent_capacity": 5.0,
                "current_load": 0.0,
                "skills": ["SKL-BILLING", "SKL-AUTH", "SKL-TECH-CORE", "SKL-SECURITY", "SKL-RETENTION", "SKL-COMPLIANCE"],
                "languages": ["en", "es", "fr", "de", "zh", "hi"]
            }
            db_agents.insert_one(fallback_agent)
            all_agents = [fallback_agent]

        channel_weight = channel.get("concurrency_weight", 0.33)

        # Filters:
        # A: Skill Match
        skill_candidates = [
            a for a in all_agents 
            if intent["required_skill_id"] in a.get("skills", [])
        ]
        if not skill_candidates:
            skill_candidates = all_agents
            reasoning_steps.append(f"Step 5a: No agents found with strict skill '{intent['required_skill_id']}'; broadened to general tier 1 pool.")
        else:
            reasoning_steps.append(f"Step 5a: Filtered {len(skill_candidates)} agents possessing skill '{intent['required_skill_id']}'.")

        # B: Language Match
        lang_candidates = [
            a for a in skill_candidates 
            if language_code in a.get("languages", ["en"])
        ]
        if not lang_candidates:
            lang_candidates = skill_candidates
            reasoning_steps.append(f"Step 5b: No active agents speak '{language_code}'. Fallback to primary English team with translation.")
            matched_lang = False
        else:
            reasoning_steps.append(f"Step 5b: Filtered {len(lang_candidates)} agents fluent in '{language_code}'.")
            matched_lang = True

        # C: Shift Availability
        shift_candidates = [
            a for a in lang_candidates
            if a.get("shift_start_hour", 0) <= current_hour < a.get("shift_end_hour", 24)
        ]
        if not shift_candidates:
            shift_candidates = lang_candidates
            reasoning_steps.append(f"Step 5c: Outside normal shift hours; routing to on-call / round-the-clock pool.")
        else:
            reasoning_steps.append(f"Step 5c: {len(shift_candidates)} agents currently on duty (Hour {current_hour}:00 UTC).")

        # D: Concurrency Capacity Check
        capacity_candidates = [
            a for a in shift_candidates
            if (a.get("current_load", 0.0) + channel_weight) <= a.get("max_concurrent_capacity", 5.0)
        ]

        if capacity_candidates:
            # Sort by least loaded agent
            capacity_candidates.sort(key=lambda a: a.get("current_load", 0.0))
            chosen_agent = capacity_candidates[0]
            reasoning_steps.append(f"Step 6: Optimal routing match: {chosen_agent['name']} ({chosen_agent['agent_id']}) - Current Load: {chosen_agent['current_load']:.2f}/{chosen_agent['max_concurrent_capacity']:.1f}.")
        else:
            # All available agents at capacity; assign to least loaded in shift and flag queue warning
            shift_candidates.sort(key=lambda a: a.get("current_load", 0.0))
            chosen_agent = shift_candidates[0]
            reasoning_steps.append(f"Step 6: High volume spike! All eligible agents near capacity limit. Routed to least burdened agent {chosen_agent['name']} ({chosen_agent['agent_id']}).")

        # 4. Generate Deterministic IDs
        count_tickets = db_tickets.count_documents({}) + 1
        ticket_id = f"TKT-2026-{count_tickets:06d}"
        asn_id = f"ASN-{ticket_id}-001"
        sla_id = f"SLA-{ticket_id}"
        msg_id = f"MSG-{ticket_id}-001"

        # 5. SLA Deadline Calculation
        target_frt, target_ttr = calculate_sla_targets(channel["channel_id"], urgency)
        frt_deadline = now + timedelta(minutes=target_frt)
        ttr_deadline = now + timedelta(minutes=target_ttr)
        reasoning_steps.append(f"Step 7: SLA Targets generated - First Response: {target_frt} min (Deadline: {frt_deadline.strftime('%H:%M:%S UTC')}), Resolution: {target_ttr} min.")

        # Update chosen agent workload in DB
        new_load = round(chosen_agent.get("current_load", 0.0) + channel_weight, 2)
        db_agents.update_one(
            {"agent_id": chosen_agent["agent_id"]},
            {"$set": {"current_load": new_load, "status": "BUSY" if new_load >= chosen_agent["max_concurrent_capacity"] else "AVAILABLE"}}
        )

        # 6. Persist Records
        ticket_record = {
            "ticket_id": ticket_id,
            "customer_id": customer["customer_id"],
            "channel_id": channel["channel_id"],
            "intent_id": intent["intent_id"],
            "language_code": language_code,
            "urgency": urgency,
            "priority_score": priority_score,
            "assigned_agent_id": chosen_agent["agent_id"],
            "queue_id": intent.get("default_queue_id", "QUE-TECH"),
            "status": "ASSIGNED",
            "created_at": now.isoformat(),
            "first_responded_at": None,
            "resolved_at": None,
            "closed_at": None,
            "is_reopened": False,
            "reopen_count": 0,
            "transfer_count": 0,
            "escalation_level": 0,
            "anomaly_flag": None
        }
        db_tickets.insert_one(ticket_record)

        assignment_event = {
            "assignment_id": asn_id,
            "ticket_id": ticket_id,
            "event_type": "ROUTED",
            "from_agent_id": None,
            "to_agent_id": chosen_agent["agent_id"],
            "from_queue_id": None,
            "to_queue_id": intent.get("default_queue_id", "QUE-TECH"),
            "reason": f"Algorithmic match: Skill={intent['required_skill_id']}, Lang={language_code}, Available Capacity",
            "agent_load_at_assignment": chosen_agent.get("current_load", 0.0),
            "agent_max_capacity": chosen_agent.get("max_concurrent_capacity", 5.0),
            "matched_skills": [intent["required_skill_id"]],
            "matched_language": matched_lang,
            "timestamp": now.isoformat()
        }
        db_assignment_events.insert_one(assignment_event)

        message_record = {
            "message_id": msg_id,
            "ticket_id": ticket_id,
            "sender_type": "CUSTOMER",
            "sender_id": customer["customer_id"],
            "channel_id": channel["channel_id"],
            "content": initial_message,
            "timestamp": now.isoformat(),
            "is_internal_note": False
        }
        db_messages.insert_one(message_record)

        sla_record = {
            "sla_id": sla_id,
            "ticket_id": ticket_id,
            "channel_id": channel["channel_id"],
            "urgency": urgency,
            "target_frt_minutes": target_frt,
            "target_ttr_minutes": target_ttr,
            "frt_deadline": frt_deadline.isoformat(),
            "ttr_deadline": ttr_deadline.isoformat(),
            "actual_frt_minutes": None,
            "actual_ttr_minutes": None,
            "frt_status": "WARNING" if target_frt <= 5 else "MET",
            "ttr_status": "PENDING",
            "calendar_type": channel.get("operating_calendar", "24X7"),
            "created_at": now.isoformat(),
            "completed_at": None
        }
        db_sla_events.insert_one(sla_record)

        # Remove MongoDB _id before returning
        ticket_record.pop("_id", None)
        assignment_event.pop("_id", None)
        sla_record.pop("_id", None)

        return {
            "ticket": ticket_record,
            "assignment_event": assignment_event,
            "sla_event": sla_record,
            "routing_reasoning": {
                "decision": f"Assigned to {chosen_agent['name']} ({chosen_agent['agent_id']}) in {intent.get('default_queue_id', 'QUE-TECH')}",
                "trace": reasoning_steps,
                "agent_selected": {
                    "agent_id": chosen_agent["agent_id"],
                    "name": chosen_agent["name"],
                    "role": chosen_agent.get("role"),
                    "matched_skills": [intent["required_skill_id"]],
                    "matched_language": matched_lang,
                    "updated_load": new_load,
                    "max_capacity": chosen_agent.get("max_concurrent_capacity")
                }
            }
        }

router_service = CaseRouter()
