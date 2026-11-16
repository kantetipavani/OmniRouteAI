"""
Deterministic Synthetic Data Generator for OmniRoute.
Implements granular domain rules, deterministic zero-padded IDs, edge case injections,
and separate ground truth outputs.
"""
import random
import hashlib
import json
import csv
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Tuple

from app.models.dictionary import DATA_DICTIONARY

MASTER_CHANNELS = [
    {
        "channel_id": "CH-EMAIL",
        "name": "Email Support",
        "type": "EMAIL",
        "concurrency_weight": 0.20,
        "is_realtime": False,
        "operating_calendar": "BUSINESS_HOURS",
        "default_frt_minutes": 120,
        "default_ttr_minutes": 1440
    },
    {
        "channel_id": "CH-CHAT",
        "name": "Live Chat",
        "type": "CHAT",
        "concurrency_weight": 0.33,
        "is_realtime": True,
        "operating_calendar": "24X7",
        "default_frt_minutes": 5,
        "default_ttr_minutes": 45
    },
    {
        "channel_id": "CH-PHONE",
        "name": "Phone Hotline",
        "type": "PHONE",
        "concurrency_weight": 1.00,
        "is_realtime": True,
        "operating_calendar": "24X7",
        "default_frt_minutes": 1,
        "default_ttr_minutes": 20
    }
]

MASTER_LANGUAGES = [
    {"language_code": "en", "name": "English", "is_active": True},
    {"language_code": "es", "name": "Spanish", "is_active": True},
    {"language_code": "fr", "name": "French", "is_active": True},
    {"language_code": "de", "name": "German", "is_active": True},
    {"language_code": "zh", "name": "Mandarin", "is_active": True},
    {"language_code": "hi", "name": "Hindi", "is_active": True}
]

MASTER_SKILLS = [
    {"skill_id": "SKL-BILLING", "name": "Billing & Invoicing", "tier_level": 1},
    {"skill_id": "SKL-AUTH", "name": "Authentication & SSO", "tier_level": 2},
    {"skill_id": "SKL-TECH-CORE", "name": "Core Platform Engineering", "tier_level": 2},
    {"skill_id": "SKL-SECURITY", "name": "Security & Forensics", "tier_level": 3},
    {"skill_id": "SKL-RETENTION", "name": "Customer Retention", "tier_level": 1},
    {"skill_id": "SKL-COMPLIANCE", "name": "GDPR & Privacy Compliance", "tier_level": 3}
]

MASTER_QUEUES = [
    {"queue_id": "QUE-BILLING", "name": "Billing Queue", "target_skill_id": "SKL-BILLING", "channel_id": "CH-EMAIL", "max_wait_time_minutes": 60, "escalation_queue_id": "QUE-TIER2"},
    {"queue_id": "QUE-TECH", "name": "Technical Support Queue", "target_skill_id": "SKL-TECH-CORE", "channel_id": "CH-CHAT", "max_wait_time_minutes": 15, "escalation_queue_id": "QUE-TIER2"},
    {"queue_id": "QUE-SECURITY", "name": "Security Incidents Queue", "target_skill_id": "SKL-SECURITY", "channel_id": "CH-PHONE", "max_wait_time_minutes": 2, "escalation_queue_id": "QUE-EXEC"},
    {"queue_id": "QUE-RETENTION", "name": "Retention & Churn Queue", "target_skill_id": "SKL-RETENTION", "channel_id": "CH-CHAT", "max_wait_time_minutes": 10, "escalation_queue_id": "QUE-TIER2"},
    {"queue_id": "QUE-COMPLIANCE", "name": "Privacy & Legal Queue", "target_skill_id": "SKL-COMPLIANCE", "channel_id": "CH-EMAIL", "max_wait_time_minutes": 120, "escalation_queue_id": "QUE-EXEC"},
    {"queue_id": "QUE-TIER2", "name": "Tier 2 Engineering Queue", "target_skill_id": "SKL-TECH-CORE", "channel_id": "CH-CHAT", "max_wait_time_minutes": 30, "escalation_queue_id": "QUE-EXEC"},
    {"queue_id": "QUE-EXEC", "name": "Executive Escalation Queue", "target_skill_id": "SKL-SECURITY", "channel_id": "CH-PHONE", "max_wait_time_minutes": 5, "escalation_queue_id": None}
]

MASTER_INTENTS = [
    {
        "intent_id": "INT-001",
        "name": "BILLING_DISPUTE",
        "category": "BILLING",
        "base_urgency": "MEDIUM",
        "required_skill_id": "SKL-BILLING",
        "default_queue_id": "QUE-BILLING"
    },
    {
        "intent_id": "INT-002",
        "name": "AUTH_LOGIN_ISSUE",
        "category": "ACCOUNT",
        "base_urgency": "HIGH",
        "required_skill_id": "SKL-AUTH",
        "default_queue_id": "QUE-TECH"
    },
    {
        "intent_id": "INT-003",
        "name": "TECHNICAL_CRASH",
        "category": "TECHNICAL",
        "base_urgency": "HIGH",
        "required_skill_id": "SKL-TECH-CORE",
        "default_queue_id": "QUE-TECH"
    },
    {
        "intent_id": "INT-004",
        "name": "SUBSCRIPTION_CANCELLATION",
        "category": "ACCOUNT",
        "base_urgency": "LOW",
        "required_skill_id": "SKL-RETENTION",
        "default_queue_id": "QUE-RETENTION"
    },
    {
        "intent_id": "INT-005",
        "name": "FEATURE_REQUEST",
        "category": "PRODUCT",
        "base_urgency": "LOW",
        "required_skill_id": "SKL-TECH-CORE",
        "default_queue_id": "QUE-TECH"
    },
    {
        "intent_id": "INT-006",
        "name": "DATA_EXPORT_GDPR",
        "category": "SECURITY",
        "base_urgency": "MEDIUM",
        "required_skill_id": "SKL-COMPLIANCE",
        "default_queue_id": "QUE-COMPLIANCE"
    },
    {
        "intent_id": "INT-007",
        "name": "SECURITY_BREACH_SUSPICION",
        "category": "SECURITY",
        "base_urgency": "CRITICAL",
        "required_skill_id": "SKL-SECURITY",
        "default_queue_id": "QUE-SECURITY"
    }
]

MASTER_PRIORITY_RULES = [
    {"rule_id": "RULE-001", "intent_id": "INT-007", "customer_tier": "ANY", "calculated_urgency": "CRITICAL", "is_safety_critical": True, "min_urgency_floor": "CRITICAL"},
    {"rule_id": "RULE-002", "intent_id": "INT-003", "customer_tier": "ENTERPRISE", "calculated_urgency": "CRITICAL", "is_safety_critical": False, "min_urgency_floor": "HIGH"},
    {"rule_id": "RULE-003", "intent_id": "INT-003", "customer_tier": "PREMIUM", "calculated_urgency": "HIGH", "is_safety_critical": False, "min_urgency_floor": "MEDIUM"},
    {"rule_id": "RULE-004", "intent_id": "INT-003", "customer_tier": "STANDARD", "calculated_urgency": "MEDIUM", "is_safety_critical": False, "min_urgency_floor": "LOW"},
    {"rule_id": "RULE-005", "intent_id": "INT-002", "customer_tier": "ENTERPRISE", "calculated_urgency": "HIGH", "is_safety_critical": False, "min_urgency_floor": "MEDIUM"},
    {"rule_id": "RULE-006", "intent_id": "INT-001", "customer_tier": "ENTERPRISE", "calculated_urgency": "HIGH", "is_safety_critical": False, "min_urgency_floor": "LOW"},
    {"rule_id": "RULE-007", "intent_id": "INT-006", "customer_tier": "ANY", "calculated_urgency": "HIGH", "is_safety_critical": True, "min_urgency_floor": "HIGH"},
    {"rule_id": "RULE-008", "intent_id": "INT-004", "customer_tier": "ANY", "calculated_urgency": "LOW", "is_safety_critical": False, "min_urgency_floor": "LOW"},
    {"rule_id": "RULE-009", "intent_id": "INT-005", "customer_tier": "ANY", "calculated_urgency": "LOW", "is_safety_critical": False, "min_urgency_floor": "LOW"}
]

FIRST_NAMES = ["Liam", "Olivia", "Noah", "Emma", "Oliver", "Charlotte", "Elijah", "Amelia", "James", "Sophia", "Aarav", "Priya", "Carlos", "Elena", "Lucas", "Mei", "Hiroshi", "Fatima", "Astrid", "Mateo"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Sharma", "Patel", "Chen", "Wang", "Müller", "Dubois", "Kim", "Tanaka", "Silva", "Santos"]

SAMPLE_MESSAGES_BY_INTENT = {
    "INT-001": [
        "I was charged twice for invoice #9042 on my credit card.",
        "There is an unexpected $450 enterprise fee on our monthly statement.",
        "Need a VAT invoice copy and credit note for our accounting department."
    ],
    "INT-002": [
        "SAML SSO is returning 401 Unauthorized for all Okta users.",
        "Password reset email is not arriving in our corporate inboxes.",
        "MFA prompt keeps rejecting valid TOTP codes after the latest authenticator update."
    ],
    "INT-003": [
        "Server returned HTTP 500 internal crash on POST /api/v2/ingest.",
        "Mobile app crashes immediately on launch on iOS 18 devices.",
        "Database pool exhausted causing total pipeline outage for our US-East region."
    ],
    "INT-004": [
        "We are downsizing operations and request cancelling subscription effective next cycle.",
        "Please cancel auto-renew on account ACC-8819.",
        "Can we downgrade our plan from Enterprise to Standard without penalty?"
    ],
    "INT-005": [
        "Requesting ability to export audit logs directly to AWS S3 bucket.",
        "Would love dark mode support and custom webhook retry policies.",
        "Is there a roadmap feature for multi-region active-active read replicas?"
    ],
    "INT-006": [
        "Formal GDPR Article 17 request to export and purge all personal customer records.",
        "Compliance audit requires full data processing agreement and tenant data archive.",
        "Need complete export of all user activity and consent logs in JSON format."
    ],
    "INT-007": [
        "CRITICAL: Detected anomalous credential stuffing attacks against production API keys.",
        "Suspicious unauthorized administrative token generated from unknown foreign IP address.",
        "Security incident alert: Database dump link posted on external paste site."
    ]
}

def compute_priority_score(tier: str, urgency: str) -> float:
    urgency_weights = {"LOW": 20.0, "MEDIUM": 45.0, "HIGH": 70.0, "CRITICAL": 95.0}
    tier_multipliers = {"STANDARD": 1.0, "PREMIUM": 1.1, "ENTERPRISE": 1.25}
    base = urgency_weights.get(urgency, 30.0)
    mult = tier_multipliers.get(tier, 1.0)
    return round(min(100.0, base * mult), 2)

def calculate_sla_targets(channel_id: str, urgency: str) -> Tuple[int, int]:
    base_channel = next(c for c in MASTER_CHANNELS if c["channel_id"] == channel_id)
    frt_base = base_channel["default_frt_minutes"]
    ttr_base = base_channel["default_ttr_minutes"]
    
    urgency_factor = {
        "CRITICAL": 0.25,
        "HIGH": 0.50,
        "MEDIUM": 1.00,
        "LOW": 2.00
    }.get(urgency, 1.0)
    
    frt = max(1, int(frt_base * urgency_factor))
    ttr = max(frt + 5, int(ttr_base * urgency_factor))
    return frt, ttr

class SyntheticDataGenerator:
    def __init__(self, seed: int = 20261022):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_all(self, scale: str = "starter") -> Dict[str, Any]:
        """
        Scale options:
        - "starter": 1,000 tickets, 25 agents, 3,500 messages, 14 days
        - "full": 30,000 tickets, 100 agents, 100,000 messages, 90 days
        """
        self.rng.seed(self.seed)
        
        if scale == "full":
            num_agents = 100
            num_customers = 5000
            num_tickets = 30000
            num_days = 90
        else:
            num_agents = 25
            num_customers = 400
            num_tickets = 1000
            num_days = 14

        base_time = datetime(2026, 8, 1, 8, 0, 0, tzinfo=timezone.utc)

        # 1. Generate Master Customers
        customers = []
        for i in range(1, num_customers + 1):
            fn = self.rng.choice(FIRST_NAMES)
            ln = self.rng.choice(LAST_NAMES)
            tier = self.rng.choices(["STANDARD", "PREMIUM", "ENTERPRISE"], weights=[0.65, 0.25, 0.10])[0]
            pref_lang = self.rng.choices(["en", "es", "fr", "de", "zh", "hi"], weights=[0.60, 0.15, 0.08, 0.07, 0.05, 0.05])[0]
            cust_created = base_time - timedelta(days=self.rng.randint(30, 365))
            customers.append({
                "customer_id": f"CUST-{i:06d}",
                "name": f"{fn} {ln}",
                "email": f"{fn.lower()}.{ln.lower()}{i}@example.com",
                "phone": f"+1{self.rng.randint(200, 999)}{self.rng.randint(1000000, 9999999)}",
                "tier": tier,
                "preferred_language": pref_lang,
                "created_at": cust_created.isoformat()
            })

        # 2. Generate Master Agents
        agents = []
        all_skill_ids = [s["skill_id"] for s in MASTER_SKILLS]
        for i in range(1, num_agents + 1):
            fn = self.rng.choice(FIRST_NAMES)
            ln = self.rng.choice(LAST_NAMES)
            role = self.rng.choices(["SUPPORT_AGENT", "SENIOR_AGENT", "SPECIALIST", "TEAM_LEAD"], weights=[0.55, 0.25, 0.15, 0.05])[0]
            assigned_skills = list(set([self.rng.choice(all_skill_ids) for _ in range(self.rng.randint(1, 3))]))
            # Language competencies (all know English; some know secondary languages)
            agent_langs = ["en"]
            if self.rng.random() < 0.4:
                agent_langs.append(self.rng.choice(["es", "fr", "de", "zh", "hi"]))
            
            # Shifts
            shift_type = self.rng.choices(["MORNING", "EVENING", "NIGHT"], weights=[0.60, 0.25, 0.15])[0]
            if shift_type == "MORNING":
                s_start, s_end = 8, 16
            elif shift_type == "EVENING":
                s_start, s_end = 16, 24
            else:
                s_start, s_end = 0, 8

            max_cap = 5.0 if role in ["SUPPORT_AGENT", "SENIOR_AGENT"] else 4.0
            agents.append({
                "agent_id": f"AGT-{i:06d}",
                "name": f"{fn} {ln}",
                "email": f"{fn.lower()}.{ln.lower()}@support.company.internal",
                "role": role,
                "status": "AVAILABLE",
                "shift_start_hour": s_start,
                "shift_end_hour": s_end,
                "timezone": "UTC",
                "max_concurrent_capacity": max_cap,
                "current_load": 0.0,
                "skills": assigned_skills,
                "languages": agent_langs
            })

        # Index agents for fast lookup
        agent_by_id = {a["agent_id"]: a for a in agents}

        # 3. Generate Tickets, Messages, AssignmentEvents, SLAEvents, Resolutions, and Anomalies
        tickets = []
        messages = []
        assignment_events = []
        sla_events = []
        resolutions = []
        anomalies = []

        # Target anomaly counts for edge cases (e.g. 5 distinct edge case categories)
        anomaly_targets = {
            "CAPACITY_EXCEEDED": max(2, int(num_tickets * 0.015)),
            "CALENDAR_IGNORED": max(2, int(num_tickets * 0.015)),
            "HISTORY_LOST": max(2, int(num_tickets * 0.010)),
            "TRANSFER_LOOP": max(2, int(num_tickets * 0.010)),
            "SAFETY_OVERRIDE_VIOLATION": max(2, int(num_tickets * 0.010))
        }
        injected_counts = {k: 0 for k in anomaly_targets}

        for t_idx in range(1, num_tickets + 1):
            ticket_id = f"TKT-2026-{t_idx:06d}"
            customer = self.rng.choice(customers)
            channel = self.rng.choices(MASTER_CHANNELS, weights=[0.45, 0.40, 0.15])[0]
            intent = self.rng.choice(MASTER_INTENTS)
            lang = customer["preferred_language"] if self.rng.random() < 0.9 else self.rng.choice(MASTER_LANGUAGES)["language_code"]
            
            # Timestamp generation distributed across num_days
            day_offset = self.rng.uniform(0, num_days)
            ticket_time = base_time + timedelta(days=day_offset, hours=self.rng.uniform(0, 24))
            
            # Decide urgency from priority rules
            matching_rule = next((r for r in MASTER_PRIORITY_RULES if r["intent_id"] == intent["intent_id"] and (r["customer_tier"] == customer["tier"] or r["customer_tier"] == "ANY")), None)
            if matching_rule:
                urgency = matching_rule["calculated_urgency"]
            else:
                urgency = intent["base_urgency"]

            # Edge Case 5 Check: SAFETY_OVERRIDE_VIOLATION
            # If this is a safety critical intent and we still need to inject anomaly 5:
            is_anomaly_safety = False
            if matching_rule and matching_rule.get("is_safety_critical") and injected_counts["SAFETY_OVERRIDE_VIOLATION"] < anomaly_targets["SAFETY_OVERRIDE_VIOLATION"]:
                urgency = "LOW"  # Deliberate violation of safety floor!
                is_anomaly_safety = True
                injected_counts["SAFETY_OVERRIDE_VIOLATION"] += 1
                anomalies.append({
                    "anomaly_id": f"ANO-{len(anomalies)+1:05d}",
                    "ticket_id": ticket_id,
                    "issue_type": "SAFETY_OVERRIDE_VIOLATION",
                    "severity": "CRITICAL",
                    "entity_id": matching_rule["rule_id"],
                    "description": f"Ticket {ticket_id} with safety-critical intent {intent['name']} was classified as LOW urgency, violating safety floor {matching_rule['min_urgency_floor']}.",
                    "expected_behavior": f"Urgency must be at or above safety floor '{matching_rule['min_urgency_floor']}'.",
                    "actual_behavior": "Urgency downgraded to LOW without authorization.",
                    "root_cause": "Misconfigured client rule override bypass.",
                    "suggested_remediation": "Enforce server-side immutable policy floor on safety-critical intent taxonomy.",
                    "timestamp": ticket_time.isoformat()
                })

            priority_score = compute_priority_score(customer["tier"], urgency)

            # Route agent
            eligible_agents = [
                a for a in agents
                if intent["required_skill_id"] in a["skills"] and lang in a["languages"]
            ]
            if not eligible_agents:
                eligible_agents = [a for a in agents if intent["required_skill_id"] in a["skills"]]
            if not eligible_agents:
                eligible_agents = agents

            assigned_agent = self.rng.choice(eligible_agents)

            # Edge Case 1 Check: CAPACITY_EXCEEDED
            is_anomaly_capacity = False
            if injected_counts["CAPACITY_EXCEEDED"] < anomaly_targets["CAPACITY_EXCEEDED"] and self.rng.random() < 0.15:
                # Force assignment to an agent who already has excessive load
                assigned_agent["current_load"] = assigned_agent["max_concurrent_capacity"] + 2.5
                is_anomaly_capacity = True
                injected_counts["CAPACITY_EXCEEDED"] += 1
                anomalies.append({
                    "anomaly_id": f"ANO-{len(anomalies)+1:05d}",
                    "ticket_id": ticket_id,
                    "issue_type": "CAPACITY_EXCEEDED",
                    "severity": "HIGH",
                    "entity_id": assigned_agent["agent_id"],
                    "description": f"Agent {assigned_agent['agent_id']} assigned ticket {ticket_id} despite current load {assigned_agent['current_load']:.1f} exceeding maximum limit {assigned_agent['max_concurrent_capacity']:.1f}.",
                    "expected_behavior": "Routing engine must reject or re-queue assignments when agent load >= max concurrency limit.",
                    "actual_behavior": f"Assigned to {assigned_agent['agent_id']} under capacity overflow.",
                    "root_cause": "Race condition in concurrency locking during burst arrival.",
                    "suggested_remediation": "Implement distributed atomic increment / pessimistic concurrency reservation.",
                    "timestamp": ticket_time.isoformat()
                })
            else:
                assigned_agent["current_load"] = min(assigned_agent["max_concurrent_capacity"], round(assigned_agent["current_load"] + channel["concurrency_weight"], 2))

            # Assignment Event
            matched_skills = [s for s in assigned_agent["skills"] if s == intent["required_skill_id"]]
            matched_lang = lang in assigned_agent["languages"]
            asn_id = f"ASN-{ticket_id}-001"
            assignment_events.append({
                "assignment_id": asn_id,
                "ticket_id": ticket_id,
                "event_type": "ROUTED",
                "from_agent_id": None,
                "to_agent_id": assigned_agent["agent_id"],
                "from_queue_id": None,
                "to_queue_id": intent["default_queue_id"],
                "reason": "Optimal skill, language and shift capacity match",
                "agent_load_at_assignment": assigned_agent["current_load"],
                "agent_max_capacity": assigned_agent["max_concurrent_capacity"],
                "matched_skills": matched_skills if matched_skills else [intent["required_skill_id"]],
                "matched_language": matched_lang,
                "timestamp": ticket_time.isoformat()
            })

            # Messages
            initial_msg_text = self.rng.choice(SAMPLE_MESSAGES_BY_INTENT.get(intent["intent_id"], ["Customer support request."]))
            messages.append({
                "message_id": f"MSG-{ticket_id}-001",
                "ticket_id": ticket_id,
                "sender_type": "CUSTOMER",
                "sender_id": customer["customer_id"],
                "channel_id": channel["channel_id"],
                "content": initial_msg_text,
                "timestamp": ticket_time.isoformat(),
                "is_internal_note": False
            })

            # SLA targets
            target_frt, target_ttr = calculate_sla_targets(channel["channel_id"], urgency)
            frt_deadline = ticket_time + timedelta(minutes=target_frt)
            ttr_deadline = ticket_time + timedelta(minutes=target_ttr)

            # Realistic response and resolution times
            mean_frt = max(1.0, target_frt * 0.75)
            first_response_delay = self.rng.expovariate(1.0 / mean_frt)
            first_responded_at = ticket_time + timedelta(minutes=first_response_delay)
            
            # Agent response message
            messages.append({
                "message_id": f"MSG-{ticket_id}-002",
                "ticket_id": ticket_id,
                "sender_type": "AGENT",
                "sender_id": assigned_agent["agent_id"],
                "channel_id": channel["channel_id"],
                "content": f"Hello {customer['name']}, thank you for reaching out regarding {intent['name'].replace('_', ' ').lower()}. I am actively investigating this for you.",
                "timestamp": first_responded_at.isoformat(),
                "is_internal_note": False
            })

            # Determine ticket lifecycle outcome
            # Edge Case 4: TRANSFER_LOOP (AGT_A -> AGT_B -> AGT_A -> AGT_B)
            is_transfer_loop = False
            transfer_count = 0
            if injected_counts["TRANSFER_LOOP"] < anomaly_targets["TRANSFER_LOOP"] and self.rng.random() < 0.05:
                is_transfer_loop = True
                injected_counts["TRANSFER_LOOP"] += 1
                second_agent = next(a for a in agents if a["agent_id"] != assigned_agent["agent_id"])
                transfer_count = 4
                
                # Create transfer bounce events
                t_time1 = first_responded_at + timedelta(minutes=10)
                assignment_events.append({
                    "assignment_id": f"ASN-{ticket_id}-002",
                    "ticket_id": ticket_id,
                    "event_type": "TRANSFERRED",
                    "from_agent_id": assigned_agent["agent_id"],
                    "to_agent_id": second_agent["agent_id"],
                    "from_queue_id": intent["default_queue_id"],
                    "to_queue_id": "QUE-TIER2",
                    "reason": "Escalated for deeper investigation",
                    "agent_load_at_assignment": second_agent["current_load"],
                    "agent_max_capacity": second_agent["max_concurrent_capacity"],
                    "matched_skills": [intent["required_skill_id"]],
                    "matched_language": True,
                    "timestamp": t_time1.isoformat()
                })
                t_time2 = t_time1 + timedelta(minutes=15)
                assignment_events.append({
                    "assignment_id": f"ASN-{ticket_id}-003",
                    "ticket_id": ticket_id,
                    "event_type": "TRANSFERRED",
                    "from_agent_id": second_agent["agent_id"],
                    "to_agent_id": assigned_agent["agent_id"],
                    "from_queue_id": "QUE-TIER2",
                    "to_queue_id": intent["default_queue_id"],
                    "reason": "Returned to frontline owner",
                    "agent_load_at_assignment": assigned_agent["current_load"],
                    "agent_max_capacity": assigned_agent["max_concurrent_capacity"],
                    "matched_skills": [intent["required_skill_id"]],
                    "matched_language": True,
                    "timestamp": t_time2.isoformat()
                })
                t_time3 = t_time2 + timedelta(minutes=15)
                assignment_events.append({
                    "assignment_id": f"ASN-{ticket_id}-004",
                    "ticket_id": ticket_id,
                    "event_type": "TRANSFERRED",
                    "from_agent_id": assigned_agent["agent_id"],
                    "to_agent_id": second_agent["agent_id"],
                    "from_queue_id": intent["default_queue_id"],
                    "to_queue_id": "QUE-TIER2",
                    "reason": "Re-escalated due to unclear root cause",
                    "agent_load_at_assignment": second_agent["current_load"],
                    "agent_max_capacity": second_agent["max_concurrent_capacity"],
                    "matched_skills": [intent["required_skill_id"]],
                    "matched_language": True,
                    "timestamp": t_time3.isoformat()
                })
                anomalies.append({
                    "anomaly_id": f"ANO-{len(anomalies)+1:05d}",
                    "ticket_id": ticket_id,
                    "issue_type": "TRANSFER_LOOP",
                    "severity": "HIGH",
                    "entity_id": ticket_id,
                    "description": f"Ticket {ticket_id} entered an oscillating transfer loop between {assigned_agent['agent_id']} and {second_agent['agent_id']}.",
                    "expected_behavior": "Tickets must not bounce between identical agents more than once without manager intervention.",
                    "actual_behavior": f"4 recursive transfer hops logged without progressive resolution.",
                    "root_cause": "Ambiguous ownership taxonomy between Tier 1 and Tier 2 queues.",
                    "suggested_remediation": "Add loop-detection circuit breaker; prevent re-transfer to previous owner without override.",
                    "timestamp": t_time3.isoformat()
                })

            # Edge Case 3: HISTORY_LOST
            is_history_lost = False
            is_reopened = False
            reopen_count = 0
            if injected_counts["HISTORY_LOST"] < anomaly_targets["HISTORY_LOST"] and self.rng.random() < 0.04:
                is_history_lost = True
                is_reopened = True
                reopen_count = 1
                injected_counts["HISTORY_LOST"] += 1
                anomalies.append({
                    "anomaly_id": f"ANO-{len(anomalies)+1:05d}",
                    "ticket_id": ticket_id,
                    "issue_type": "HISTORY_LOST",
                    "severity": "CRITICAL",
                    "entity_id": ticket_id,
                    "description": f"Reopened ticket {ticket_id} lost historical message context and audit trail references during state transition.",
                    "expected_behavior": "Reopening a ticket must append a REOPEN event and preserve all prior threaded history.",
                    "actual_behavior": "Historical assignment events were truncated/detached in legacy store.",
                    "root_cause": "Destructive in-place overwrite query on reopen API endpoint.",
                    "suggested_remediation": "Migrate state machine to strictly append-only event sourcing pattern.",
                    "timestamp": (first_responded_at + timedelta(hours=24)).isoformat()
                })

            # Resolution calculation
            mean_ttr = max(2.0, target_ttr * 0.70)
            resolution_delay = first_response_delay + self.rng.expovariate(1.0 / mean_ttr)
            resolved_at = ticket_time + timedelta(minutes=resolution_delay)
            closed_at = resolved_at + timedelta(hours=self.rng.randint(2, 48))

            # Edge Case 2: CALENDAR_IGNORED
            is_calendar_ignored = False
            if injected_counts["CALENDAR_IGNORED"] < anomaly_targets["CALENDAR_IGNORED"] and channel["operating_calendar"] == "BUSINESS_HOURS" and self.rng.random() < 0.15:
                is_calendar_ignored = True
                injected_counts["CALENDAR_IGNORED"] += 1
                anomalies.append({
                    "anomaly_id": f"ANO-{len(anomalies)+1:05d}",
                    "ticket_id": ticket_id,
                    "issue_type": "CALENDAR_IGNORED",
                    "severity": "MEDIUM",
                    "entity_id": channel["channel_id"],
                    "description": f"Ticket {ticket_id} on {channel['name']} had SLA breach calculated across weekend/non-working hours, ignoring BUSINESS_HOURS calendar.",
                    "expected_behavior": "SLA timer must pause outside 09:00-17:00 Monday-Friday calendar.",
                    "actual_behavior": "Wall-clock 24x7 timer applied indiscriminately to business-hours channel.",
                    "root_cause": "Missing calendar provider interceptor in SLA deadline worker.",
                    "suggested_remediation": "Pass business calendar holiday/weekend exclusion schedules into SLA deadline evaluator.",
                    "timestamp": ticket_time.isoformat()
                })

            actual_frt = round(first_response_delay, 1)
            actual_ttr = round(resolution_delay, 1)
            frt_status = "MET" if actual_frt <= target_frt else "BREACHED"
            ttr_status = "MET" if actual_ttr <= target_ttr else "BREACHED"

            # SLA Event
            sla_id = f"SLA-{ticket_id}"
            sla_events.append({
                "sla_id": sla_id,
                "ticket_id": ticket_id,
                "channel_id": channel["channel_id"],
                "urgency": urgency,
                "target_frt_minutes": target_frt,
                "target_ttr_minutes": target_ttr,
                "frt_deadline": frt_deadline.isoformat(),
                "ttr_deadline": ttr_deadline.isoformat(),
                "actual_frt_minutes": actual_frt,
                "actual_ttr_minutes": actual_ttr,
                "frt_status": frt_status,
                "ttr_status": ttr_status,
                "calendar_type": channel["operating_calendar"],
                "created_at": ticket_time.isoformat(),
                "completed_at": resolved_at.isoformat()
            })

            # Resolution Record
            res_id = f"RES-{ticket_id}"
            csat = self.rng.choices([5, 4, 3, 2, 1], weights=[0.55, 0.25, 0.10, 0.05, 0.05])[0]
            resolutions.append({
                "resolution_id": res_id,
                "ticket_id": ticket_id,
                "resolved_by_agent_id": assigned_agent["agent_id"],
                "resolution_type": self.rng.choice(["FIRST_CONTACT_RESOLUTION", "ESCALATED_FIX", "WORKAROUND", "REFUND_PROCESSED", "BUG_FILED"]),
                "root_cause_category": self.rng.choice(["USER_GUIDANCE", "CONFIG_ERROR", "INFRASTRUCTURE_OUTAGE", "BILLING_DISCREPANCY", "SECURITY_ALERT", "PRODUCT_DEFECT"]),
                "notes": f"Root cause diagnosed and resolved. Customer confirmed satisfaction.",
                "customer_satisfaction_score": csat,
                "csat_feedback": "Issue resolved quickly" if csat >= 4 else "Took longer than expected",
                "resolved_at": resolved_at.isoformat()
            })

            # Final Ticket Status
            final_status = "RESOLVED" if not is_reopened else "REOPENED"
            anomaly_flag = None
            if is_anomaly_capacity:
                anomaly_flag = "CAPACITY_EXCEEDED"
            elif is_calendar_ignored:
                anomaly_flag = "CALENDAR_IGNORED"
            elif is_history_lost:
                anomaly_flag = "HISTORY_LOST"
            elif is_transfer_loop:
                anomaly_flag = "TRANSFER_LOOP"
            elif is_anomaly_safety:
                anomaly_flag = "SAFETY_OVERRIDE_VIOLATION"

            tickets.append({
                "ticket_id": ticket_id,
                "customer_id": customer["customer_id"],
                "channel_id": channel["channel_id"],
                "intent_id": intent["intent_id"],
                "language_code": lang,
                "urgency": urgency,
                "priority_score": priority_score,
                "assigned_agent_id": assigned_agent["agent_id"],
                "queue_id": intent["default_queue_id"],
                "status": final_status,
                "created_at": ticket_time.isoformat(),
                "first_responded_at": first_responded_at.isoformat(),
                "resolved_at": resolved_at.isoformat(),
                "closed_at": closed_at.isoformat(),
                "is_reopened": is_reopened,
                "reopen_count": reopen_count,
                "transfer_count": transfer_count,
                "escalation_level": 1 if is_transfer_loop else 0,
                "anomaly_flag": anomaly_flag
            })

        # Calculate dataset manifest & checksums
        manifest = {
            "scale": scale,
            "seed": self.seed,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "counts": {
                "customers": len(customers),
                "channels": len(MASTER_CHANNELS),
                "languages": len(MASTER_LANGUAGES),
                "skills": len(MASTER_SKILLS),
                "queues": len(MASTER_QUEUES),
                "intents": len(MASTER_INTENTS),
                "priority_rules": len(MASTER_PRIORITY_RULES),
                "agents": len(agents),
                "tickets": len(tickets),
                "messages": len(messages),
                "assignment_events": len(assignment_events),
                "sla_events": len(sla_events),
                "resolutions": len(resolutions),
                "ground_truth_anomalies": len(anomalies)
            },
            "anomalies_by_type": {
                k: sum(1 for a in anomalies if a["issue_type"] == k)
                for k in anomaly_targets
            }
        }

        # Deterministic Checksum of tickets
        checksum_payload = "".join([t["ticket_id"] + t["urgency"] + t["assigned_agent_id"] for t in tickets])
        manifest["dataset_sha256"] = hashlib.sha256(checksum_payload.encode()).hexdigest()

        return {
            "manifest": manifest,
            "customers": customers,
            "channels": MASTER_CHANNELS,
            "languages": MASTER_LANGUAGES,
            "skills": MASTER_SKILLS,
            "queues": MASTER_QUEUES,
            "intents": MASTER_INTENTS,
            "priority_rules": MASTER_PRIORITY_RULES,
            "agents": agents,
            "tickets": tickets,
            "messages": messages,
            "assignment_events": assignment_events,
            "sla_events": sla_events,
            "resolutions": resolutions,
            "ground_truth": anomalies
        }

    def export_to_disk(self, data: Dict[str, Any], output_dir: str = "backend/data"):
        os.makedirs(output_dir, exist_ok=True)

        # Save manifest
        with open(os.path.join(output_dir, "seed_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(data["manifest"], f, indent=2)

        # Save data dictionary
        with open(os.path.join(output_dir, "data_dictionary.json"), "w", encoding="utf-8") as f:
            json.dump(DATA_DICTIONARY, f, indent=2)

        # Save ground truth anomalies (JSON and CSV)
        with open(os.path.join(output_dir, "ground_truth.json"), "w", encoding="utf-8") as f:
            json.dump(data["ground_truth"], f, indent=2)

        if data["ground_truth"]:
            with open(os.path.join(output_dir, "ground_truth.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(data["ground_truth"][0].keys()))
                writer.writeheader()
                writer.writerows(data["ground_truth"])

        # Save all tabular entities as CSV
        tabular_keys = [
            ("customers", "customers.csv"),
            ("channels", "channels.csv"),
            ("languages", "languages.csv"),
            ("skills", "skills.csv"),
            ("queues", "queues.csv"),
            ("intents", "intents.csv"),
            ("priority_rules", "priority_rules.csv"),
            ("agents", "agents.csv"),
            ("tickets", "tickets.csv"),
            ("messages", "messages.csv"),
            ("assignment_events", "assignment_events.csv"),
            ("sla_events", "sla_events.csv"),
            ("resolutions", "resolutions.csv")
        ]

        for key, fname in tabular_keys:
            items = data.get(key, [])
            if items:
                # Convert list fields to JSON strings for CSV compatibility
                processed_items = []
                for item in items:
                    row = {}
                    for k, v in item.items():
                        if isinstance(v, (list, dict)):
                            row[k] = json.dumps(v)
                        else:
                            row[k] = v
                    processed_items.append(row)

                with open(os.path.join(output_dir, fname), "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(processed_items[0].keys()))
                    writer.writeheader()
                    writer.writerows(processed_items)
