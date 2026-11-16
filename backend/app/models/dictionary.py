"""
Complete Master Data Dictionary and Schema Specifications
for OmniRoute - Omnichannel Case Routing and SLA Management System.
"""

DATA_DICTIONARY = {
    "Customer": {
        "description": "Master table containing customer identity, subscription tier, and contact preferences.",
        "primary_key": "customer_id",
        "cardinality": "1:N with Ticket",
        "fields": {
            "customer_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^CUST-\\d{6}$ (e.g., CUST-000001)",
                "units": "Alphanumeric identifier",
                "validation_rule": "Must match regex ^CUST-\\d{6}$ and be globally unique."
            },
            "name": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Full name strings, 2-100 characters",
                "units": "Text",
                "validation_rule": "Non-empty string."
            },
            "email": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Valid RFC 5322 email addresses",
                "units": "Email string",
                "validation_rule": "Must be valid email format with domain."
            },
            "phone": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "E.164 phone format: +1XXXXXXXXXX",
                "units": "Phone number",
                "validation_rule": "Must start with + and country code."
            },
            "tier": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["STANDARD", "PREMIUM", "ENTERPRISE"],
                "units": "Categorical tier",
                "validation_rule": "Must be in allowed enum values."
            },
            "preferred_language": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["en", "es", "fr", "de", "zh", "hi"],
                "units": "ISO 639-1 code",
                "validation_rule": "Must exist in Language master table."
            },
            "created_at": {
                "type": "iso_datetime",
                "required": True,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Must precede any related Ticket created_at."
            }
        }
    },
    "Channel": {
        "description": "Master table of incoming communication channels and their operational constraints.",
        "primary_key": "channel_id",
        "cardinality": "1:N with Ticket, 1:N with SLAEvent",
        "fields": {
            "channel_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": ["CH-EMAIL", "CH-CHAT", "CH-PHONE"],
                "units": "Channel code",
                "validation_rule": "Must be one of pre-defined channel IDs."
            },
            "name": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": ["Email Support", "Live Chat", "Phone Hotline"],
                "units": "Text",
                "validation_rule": "Non-empty string."
            },
            "type": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["EMAIL", "CHAT", "PHONE"],
                "units": "Channel type",
                "validation_rule": "Matches channel category."
            },
            "concurrency_weight": {
                "type": "float",
                "required": True,
                "uniqueness": False,
                "allowed_values": "0.1 to 1.0 (Phone=1.0, Chat=0.33, Email=0.2)",
                "units": "Load multiplier",
                "validation_rule": "Range between 0.05 and 1.0."
            },
            "is_realtime": {
                "type": "boolean",
                "required": True,
                "uniqueness": False,
                "allowed_values": [True, False],
                "units": "Flag",
                "validation_rule": "True for CHAT and PHONE, False for EMAIL."
            },
            "operating_calendar": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["BUSINESS_HOURS", "24X7"],
                "units": "Calendar mode",
                "validation_rule": "EMAIL is BUSINESS_HOURS; CHAT/PHONE is 24X7 or SHIFTS."
            },
            "default_frt_minutes": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": "1 to 720 minutes",
                "units": "Minutes",
                "validation_rule": "Positive integer."
            },
            "default_ttr_minutes": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": "15 to 2880 minutes",
                "units": "Minutes",
                "validation_rule": "Must be >= default_frt_minutes."
            }
        }
    },
    "Language": {
        "description": "Master list of recognized customer and agent languages.",
        "primary_key": "language_code",
        "cardinality": "1:N with Customer, Ticket, AgentLanguage",
        "fields": {
            "language_code": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": ["en", "es", "fr", "de", "zh", "hi"],
                "units": "ISO 639-1",
                "validation_rule": "2-letter lowercase code."
            },
            "name": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": ["English", "Spanish", "French", "German", "Mandarin", "Hindi"],
                "units": "Language name",
                "validation_rule": "Properly capitalized name."
            },
            "is_active": {
                "type": "boolean",
                "required": True,
                "uniqueness": False,
                "allowed_values": [True, False],
                "units": "Status flag",
                "validation_rule": "Boolean."
            }
        }
    },
    "Skill": {
        "description": "Categorization of functional competencies required for routing cases.",
        "primary_key": "skill_id",
        "cardinality": "N:M with Agent via AgentSkill, 1:N with Intent",
        "fields": {
            "skill_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^SKL-[A-Z_]+$",
                "units": "Identifier",
                "validation_rule": "Uppercase alphanumeric identifier."
            },
            "name": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Skill names (e.g. Billing Resolution, Security Forensics)",
                "units": "Text",
                "validation_rule": "Non-empty string."
            },
            "tier_level": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": [1, 2, 3],
                "units": "Competency level",
                "validation_rule": "1=Frontline, 2=Senior, 3=Specialist/Principal."
            }
        }
    },
    "Queue": {
        "description": "Logical holding queues mapped to target skills and channels.",
        "primary_key": "queue_id",
        "cardinality": "1:N with Ticket, 1:N with AssignmentEvent",
        "fields": {
            "queue_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^QUE-[A-Z_]+$",
                "units": "Identifier",
                "validation_rule": "Uppercase identifier starting with QUE-."
            },
            "name": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Queue display name",
                "units": "Text",
                "validation_rule": "Non-empty string."
            },
            "target_skill_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid skill_id in Skill table",
                "units": "Foreign Key",
                "validation_rule": "Must exist in Skill table."
            },
            "max_wait_time_minutes": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": "1 to 120 minutes",
                "units": "Minutes",
                "validation_rule": "Positive integer."
            },
            "escalation_queue_id": {
                "type": "string",
                "required": False,
                "uniqueness": False,
                "allowed_values": "Valid queue_id or null",
                "units": "Foreign Key",
                "validation_rule": "If set, must reference an existing Queue."
            }
        }
    },
    "Intent": {
        "description": "Taxonomy of customer inquiries mapping to required skills and SLA baselines.",
        "primary_key": "intent_id",
        "cardinality": "1:N with Ticket, 1:N with PriorityRule",
        "fields": {
            "intent_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^INT-\\d{3}$ (e.g. INT-001)",
                "units": "Identifier",
                "validation_rule": "Must match regex ^INT-\\d{3}$."
            },
            "name": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": ["BILLING_DISPUTE", "AUTH_LOGIN_ISSUE", "TECHNICAL_CRASH", "SUBSCRIPTION_CANCELLATION", "FEATURE_REQUEST", "DATA_EXPORT_GDPR", "SECURITY_BREACH_SUSPICION"],
                "units": "Intent enum",
                "validation_rule": "Standard intent taxonomy name."
            },
            "category": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["BILLING", "TECHNICAL", "SECURITY", "ACCOUNT", "PRODUCT"],
                "units": "Category",
                "validation_rule": "Valid department category."
            },
            "base_urgency": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                "units": "Urgency enum",
                "validation_rule": "Must be valid urgency level."
            },
            "required_skill_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid skill_id in Skill table",
                "units": "Foreign Key",
                "validation_rule": "Must exist in Skill table."
            },
            "default_queue_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid queue_id in Queue table",
                "units": "Foreign Key",
                "validation_rule": "Must exist in Queue table."
            }
        }
    },
    "PriorityRule": {
        "description": "Conditional rule matrix calculating final ticket urgency from intent, customer tier, and safety policies.",
        "primary_key": "rule_id",
        "cardinality": "N:1 with Intent",
        "fields": {
            "rule_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^RULE-\\d{3}$",
                "units": "Identifier",
                "validation_rule": "Must match regex ^RULE-\\d{3}$."
            },
            "intent_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid intent_id in Intent table",
                "units": "Foreign Key",
                "validation_rule": "Must exist in Intent table."
            },
            "customer_tier": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["STANDARD", "PREMIUM", "ENTERPRISE", "ANY"],
                "units": "Tier enum",
                "validation_rule": "Valid tier or wildcard."
            },
            "calculated_urgency": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                "units": "Urgency enum",
                "validation_rule": "Calculated priority."
            },
            "is_safety_critical": {
                "type": "boolean",
                "required": True,
                "uniqueness": False,
                "allowed_values": [True, False],
                "units": "Flag",
                "validation_rule": "True if intent involves security, safety, or legal risks."
            },
            "min_urgency_floor": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                "units": "Urgency floor",
                "validation_rule": "For safety critical rules, min floor must be >= HIGH."
            }
        }
    },
    "Agent": {
        "description": "Customer support agents, skills, language fluency, shift times, and live capacity constraints.",
        "primary_key": "agent_id",
        "cardinality": "1:N with Ticket, 1:N with AssignmentEvent, 1:N with Resolution",
        "fields": {
            "agent_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^AGT-\\d{6}$ (e.g. AGT-000001)",
                "units": "Identifier",
                "validation_rule": "Must match regex ^AGT-\\d{6}$ and be globally unique."
            },
            "name": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Agent full name string",
                "units": "Text",
                "validation_rule": "Non-empty string."
            },
            "email": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Corporate agent email format",
                "units": "Email",
                "validation_rule": "Valid email address."
            },
            "role": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["SUPPORT_AGENT", "SENIOR_AGENT", "SPECIALIST", "TEAM_LEAD"],
                "units": "Role enum",
                "validation_rule": "Must be valid role."
            },
            "status": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["AVAILABLE", "BUSY", "ON_BREAK", "OFFLINE"],
                "units": "Presence status",
                "validation_rule": "Valid presence enum."
            },
            "shift_start_hour": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": "0 to 23",
                "units": "Hour (UTC)",
                "validation_rule": "0 <= shift_start_hour < 24."
            },
            "shift_end_hour": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": "0 to 23",
                "units": "Hour (UTC)",
                "validation_rule": "0 <= shift_end_hour < 24."
            },
            "max_concurrent_capacity": {
                "type": "float",
                "required": True,
                "uniqueness": False,
                "allowed_values": "1.0 to 10.0 concurrency units",
                "units": "Capacity units",
                "validation_rule": "Positive float representing maximum concurrent workload."
            },
            "current_load": {
                "type": "float",
                "required": True,
                "uniqueness": False,
                "allowed_values": "0.0 to 15.0",
                "units": "Load units",
                "validation_rule": "Sum of concurrency weights for assigned active tickets. Must be <= max_concurrent_capacity in normal operation."
            },
            "skills": {
                "type": "list of strings",
                "required": True,
                "uniqueness": False,
                "allowed_values": "List of valid skill_ids",
                "units": "FK reference list",
                "validation_rule": "Each skill must exist in Skill table."
            },
            "languages": {
                "type": "list of strings",
                "required": True,
                "uniqueness": False,
                "allowed_values": "List of valid language_codes",
                "units": "FK reference list",
                "validation_rule": "Each language must exist in Language table."
            }
        }
    },
    "Ticket": {
        "description": "Central transaction record for customer support cases.",
        "primary_key": "ticket_id",
        "cardinality": "1:N with Message, 1:N with AssignmentEvent, 1:1 with SLAEvent, 0..1:1 with Resolution",
        "fields": {
            "ticket_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^TKT-2026-\\d{6}$ (e.g. TKT-2026-000001)",
                "units": "Identifier",
                "validation_rule": "Must match regex ^TKT-2026-\\d{6}$."
            },
            "customer_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid customer_id in Customer table",
                "units": "Foreign Key",
                "validation_rule": "Must reference an existing Customer."
            },
            "channel_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["CH-EMAIL", "CH-CHAT", "CH-PHONE"],
                "units": "Foreign Key",
                "validation_rule": "Must reference an existing Channel."
            },
            "intent_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid intent_id in Intent table",
                "units": "Foreign Key",
                "validation_rule": "Must reference an existing Intent."
            },
            "language_code": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid language_code in Language table",
                "units": "Foreign Key",
                "validation_rule": "Must reference an existing Language."
            },
            "urgency": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                "units": "Urgency enum",
                "validation_rule": "Valid urgency value."
            },
            "priority_score": {
                "type": "float",
                "required": True,
                "uniqueness": False,
                "allowed_values": "10.0 to 100.0",
                "units": "Score",
                "validation_rule": "Weighted score based on customer tier and urgency."
            },
            "assigned_agent_id": {
                "type": "string",
                "required": False,
                "uniqueness": False,
                "allowed_values": "Valid agent_id or null",
                "units": "Foreign Key",
                "validation_rule": "If assigned, must reference Agent table."
            },
            "queue_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid queue_id in Queue table",
                "units": "Foreign Key",
                "validation_rule": "Must reference Queue table."
            },
            "status": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["NEW", "ASSIGNED", "IN_PROGRESS", "TRANSFERRED", "ESCALATED", "RESOLVED", "CLOSED", "REOPENED"],
                "units": "Lifecycle state",
                "validation_rule": "Follows defined lifecycle transitions."
            },
            "created_at": {
                "type": "iso_datetime",
                "required": True,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Base timestamp."
            },
            "first_responded_at": {
                "type": "iso_datetime",
                "required": False,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Must be >= created_at if present."
            },
            "resolved_at": {
                "type": "iso_datetime",
                "required": False,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Must be >= first_responded_at if present."
            },
            "closed_at": {
                "type": "iso_datetime",
                "required": False,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Must be >= resolved_at if present."
            },
            "is_reopened": {
                "type": "boolean",
                "required": True,
                "uniqueness": False,
                "allowed_values": [True, False],
                "units": "Flag",
                "validation_rule": "True if ticket was reopened after resolution."
            },
            "reopen_count": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": "0 to 10",
                "units": "Count",
                "validation_rule": ">= 0."
            },
            "transfer_count": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": "0 to 10",
                "units": "Count",
                "validation_rule": ">= 0."
            },
            "escalation_level": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": [0, 1, 2, 3],
                "units": "Level",
                "validation_rule": "0=Normal, 1=Tier 2, 2=Tier 3, 3=Executive."
            }
        }
    },
    "Message": {
        "description": "Threaded communication records associated with a ticket across channels.",
        "primary_key": "message_id",
        "cardinality": "N:1 with Ticket",
        "fields": {
            "message_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^MSG-TKT-2026-\\d{6}-\\d{3}$ (e.g. MSG-TKT-2026-000001-001)",
                "units": "Identifier",
                "validation_rule": "Must match regex ^MSG-TKT-2026-\\d{6}-\\d{3}$."
            },
            "ticket_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid ticket_id in Ticket table",
                "units": "Foreign Key",
                "validation_rule": "Must reference parent Ticket."
            },
            "sender_type": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["CUSTOMER", "AGENT", "SYSTEM"],
                "units": "Sender role",
                "validation_rule": "Must be valid sender enum."
            },
            "sender_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid customer_id, agent_id, or 'SYSTEM'",
                "units": "Actor ID",
                "validation_rule": "Matches sender_type reference."
            },
            "channel_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["CH-EMAIL", "CH-CHAT", "CH-PHONE"],
                "units": "Foreign Key",
                "validation_rule": "Must match Ticket channel_id."
            },
            "content": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Text message body or transcription",
                "units": "Text",
                "validation_rule": "Non-empty string."
            },
            "timestamp": {
                "type": "iso_datetime",
                "required": True,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Must be >= Ticket created_at."
            },
            "is_internal_note": {
                "type": "boolean",
                "required": True,
                "uniqueness": False,
                "allowed_values": [True, False],
                "units": "Flag",
                "validation_rule": "True only if sender_type in ('AGENT', 'SYSTEM')."
            }
        }
    },
    "AssignmentEvent": {
        "description": "Immutable audit log of routing, transfer, escalation, and assignment state changes.",
        "primary_key": "assignment_id",
        "cardinality": "N:1 with Ticket",
        "fields": {
            "assignment_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^ASN-TKT-2026-\\d{6}-\\d{3}$ (e.g. ASN-TKT-2026-000001-001)",
                "units": "Identifier",
                "validation_rule": "Must match regex ^ASN-TKT-2026-\\d{6}-\\d{3}$."
            },
            "ticket_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid ticket_id in Ticket table",
                "units": "Foreign Key",
                "validation_rule": "Must reference parent Ticket."
            },
            "event_type": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["ROUTED", "TRANSFERRED", "ESCALATED", "REASSIGNED", "CAPACITY_OVERFLOW"],
                "units": "Event enum",
                "validation_rule": "Valid assignment event type."
            },
            "from_agent_id": {
                "type": "string",
                "required": False,
                "uniqueness": False,
                "allowed_values": "Valid agent_id or null",
                "units": "Foreign Key",
                "validation_rule": "Previous agent ID if transferred or reassigned."
            },
            "to_agent_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid agent_id in Agent table",
                "units": "Foreign Key",
                "validation_rule": "Must reference assigned Agent."
            },
            "from_queue_id": {
                "type": "string",
                "required": False,
                "uniqueness": False,
                "allowed_values": "Valid queue_id or null",
                "units": "Foreign Key",
                "validation_rule": "Source queue."
            },
            "to_queue_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid queue_id in Queue table",
                "units": "Foreign Key",
                "validation_rule": "Destination queue."
            },
            "reason": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Explanation text (e.g. Skill Match, Escalation Tier 2, Capacity Rebalance)",
                "units": "Text",
                "validation_rule": "Non-empty string."
            },
            "agent_load_at_assignment": {
                "type": "float",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Workload value at moment of assignment",
                "units": "Capacity units",
                "validation_rule": ">= 0.0."
            },
            "agent_max_capacity": {
                "type": "float",
                "required": True,
                "uniqueness": False,
                "allowed_values": "1.0 to 10.0",
                "units": "Capacity units",
                "validation_rule": "> 0.0."
            },
            "matched_skills": {
                "type": "list of strings",
                "required": True,
                "uniqueness": False,
                "allowed_values": "List of skill_ids satisfied by the agent",
                "units": "FK reference list",
                "validation_rule": "Must include Ticket required skill unless overflow."
            },
            "matched_language": {
                "type": "boolean",
                "required": True,
                "uniqueness": False,
                "allowed_values": [True, False],
                "units": "Flag",
                "validation_rule": "True if agent speaks Ticket language."
            },
            "timestamp": {
                "type": "iso_datetime",
                "required": True,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Must be chronologically ascending for a ticket."
            }
        }
    },
    "SLAEvent": {
        "description": "Calculated SLA targets, response deadlines, and breach status tracking.",
        "primary_key": "sla_id",
        "cardinality": "1:1 with Ticket",
        "fields": {
            "sla_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^SLA-TKT-2026-\\d{6}$ (e.g. SLA-TKT-2026-000001)",
                "units": "Identifier",
                "validation_rule": "Must match regex ^SLA-TKT-2026-\\d{6}$."
            },
            "ticket_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Valid ticket_id in Ticket table",
                "units": "Foreign Key",
                "validation_rule": "1:1 link to Ticket."
            },
            "channel_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["CH-EMAIL", "CH-CHAT", "CH-PHONE"],
                "units": "Foreign Key",
                "validation_rule": "Must match Ticket channel_id."
            },
            "urgency": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                "units": "Urgency enum",
                "validation_rule": "Must match Ticket urgency."
            },
            "target_frt_minutes": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": "1 to 480 minutes",
                "units": "Minutes",
                "validation_rule": "Calculated from channel and urgency rules."
            },
            "target_ttr_minutes": {
                "type": "integer",
                "required": True,
                "uniqueness": False,
                "allowed_values": "10 to 2880 minutes",
                "units": "Minutes",
                "validation_rule": "Calculated target time to resolution."
            },
            "frt_deadline": {
                "type": "iso_datetime",
                "required": True,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Ticket created_at + target_frt_minutes (respecting channel calendar)."
            },
            "ttr_deadline": {
                "type": "iso_datetime",
                "required": True,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Ticket created_at + target_ttr_minutes (respecting channel calendar)."
            },
            "actual_frt_minutes": {
                "type": "float",
                "required": False,
                "uniqueness": False,
                "allowed_values": "0.1 to 10000.0",
                "units": "Minutes",
                "validation_rule": "Minutes elapsed between ticket creation and first response."
            },
            "actual_ttr_minutes": {
                "type": "float",
                "required": False,
                "uniqueness": False,
                "allowed_values": "0.5 to 20000.0",
                "units": "Minutes",
                "validation_rule": "Minutes elapsed between ticket creation and resolution."
            },
            "frt_status": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["MET", "WARNING", "BREACHED"],
                "units": "SLA Status",
                "validation_rule": "Computed: actual_frt <= target_frt => MET; otherwise BREACHED."
            },
            "ttr_status": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["MET", "WARNING", "BREACHED", "PENDING"],
                "units": "SLA Status",
                "validation_rule": "Computed: actual_ttr <= target_ttr => MET; otherwise BREACHED."
            },
            "calendar_type": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["BUSINESS_HOURS", "CALENDAR_24X7"],
                "units": "Calendar enum",
                "validation_rule": "Defines SLA clock progression."
            },
            "created_at": {
                "type": "iso_datetime",
                "required": True,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Matches Ticket created_at."
            },
            "completed_at": {
                "type": "iso_datetime",
                "required": False,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Matches Ticket resolved_at or null if pending."
            }
        }
    },
    "Resolution": {
        "description": "Final case outcome, root-cause categorization, and customer satisfaction (CSAT) score.",
        "primary_key": "resolution_id",
        "cardinality": "1:1 with Ticket",
        "fields": {
            "resolution_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Pattern: ^RES-TKT-2026-\\d{6}$ (e.g. RES-TKT-2026-000001)",
                "units": "Identifier",
                "validation_rule": "Must match regex ^RES-TKT-2026-\\d{6}$."
            },
            "ticket_id": {
                "type": "string",
                "required": True,
                "uniqueness": True,
                "allowed_values": "Valid ticket_id in Ticket table",
                "units": "Foreign Key",
                "validation_rule": "Must reference parent Ticket."
            },
            "resolved_by_agent_id": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Valid agent_id in Agent table",
                "units": "Foreign Key",
                "validation_rule": "Must reference Agent who closed the case."
            },
            "resolution_type": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["FIRST_CONTACT_RESOLUTION", "ESCALATED_FIX", "WORKAROUND", "REFUND_PROCESSED", "BUG_FILED"],
                "units": "Resolution enum",
                "validation_rule": "Valid resolution type."
            },
            "root_cause_category": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": ["USER_GUIDANCE", "CONFIG_ERROR", "INFRASTRUCTURE_OUTAGE", "BILLING_DISCREPANCY", "SECURITY_ALERT", "PRODUCT_DEFECT"],
                "units": "Category enum",
                "validation_rule": "Must be valid root-cause category."
            },
            "notes": {
                "type": "string",
                "required": True,
                "uniqueness": False,
                "allowed_values": "Resolution summary text",
                "units": "Text",
                "validation_rule": "Non-empty string."
            },
            "customer_satisfaction_score": {
                "type": "integer",
                "required": False,
                "uniqueness": False,
                "allowed_values": [1, 2, 3, 4, 5],
                "units": "CSAT Rating (1-5)",
                "validation_rule": "1=Very Dissatisfied, 5=Very Satisfied."
            },
            "csat_feedback": {
                "type": "string",
                "required": False,
                "uniqueness": False,
                "allowed_values": "Feedback commentary text",
                "units": "Text",
                "validation_rule": "Optional feedback commentary."
            },
            "resolved_at": {
                "type": "iso_datetime",
                "required": True,
                "uniqueness": False,
                "allowed_values": "ISO 8601 UTC timestamp",
                "units": "Datetime",
                "validation_rule": "Must match Ticket resolved_at."
            }
        }
    }
}
