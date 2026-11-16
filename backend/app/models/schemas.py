"""
Pydantic Schemas and Domain Models for OmniRoute.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class CustomerModel(BaseModel):
    customer_id: str
    name: str
    email: str
    phone: str
    tier: str  # STANDARD, PREMIUM, ENTERPRISE
    preferred_language: str
    created_at: str

class ChannelModel(BaseModel):
    channel_id: str
    name: str
    type: str  # EMAIL, CHAT, PHONE
    concurrency_weight: float
    is_realtime: bool
    operating_calendar: str  # BUSINESS_HOURS, 24X7
    default_frt_minutes: int
    default_ttr_minutes: int

class LanguageModel(BaseModel):
    language_code: str
    name: str
    is_active: bool

class SkillModel(BaseModel):
    skill_id: str
    name: str
    tier_level: int

class QueueModel(BaseModel):
    queue_id: str
    name: str
    target_skill_id: str
    channel_id: str
    max_wait_time_minutes: int
    escalation_queue_id: Optional[str] = None

class IntentModel(BaseModel):
    intent_id: str
    name: str
    category: str
    base_urgency: str
    required_skill_id: str
    default_queue_id: str

class PriorityRuleModel(BaseModel):
    rule_id: str
    intent_id: str
    customer_tier: str
    calculated_urgency: str
    is_safety_critical: bool
    min_urgency_floor: str

class AgentModel(BaseModel):
    agent_id: str
    name: str
    email: str
    role: str
    status: str  # AVAILABLE, BUSY, ON_BREAK, OFFLINE
    shift_start_hour: int
    shift_end_hour: int
    timezone: str = "UTC"
    max_concurrent_capacity: float
    current_load: float
    skills: List[str]
    languages: List[str]

class MessageModel(BaseModel):
    message_id: str
    ticket_id: str
    sender_type: str  # CUSTOMER, AGENT, SYSTEM
    sender_id: str
    channel_id: str
    content: str
    timestamp: str
    is_internal_note: bool = False

class AssignmentEventModel(BaseModel):
    assignment_id: str
    ticket_id: str
    event_type: str  # ROUTED, TRANSFERRED, ESCALATED, REASSIGNED, CAPACITY_OVERFLOW
    from_agent_id: Optional[str] = None
    to_agent_id: str
    from_queue_id: Optional[str] = None
    to_queue_id: str
    reason: str
    agent_load_at_assignment: float
    agent_max_capacity: float
    matched_skills: List[str]
    matched_language: bool
    timestamp: str

class SLAEventModel(BaseModel):
    sla_id: str
    ticket_id: str
    channel_id: str
    urgency: str
    target_frt_minutes: int
    target_ttr_minutes: int
    frt_deadline: str
    ttr_deadline: str
    actual_frt_minutes: Optional[float] = None
    actual_ttr_minutes: Optional[float] = None
    frt_status: str  # MET, WARNING, BREACHED
    ttr_status: str  # MET, WARNING, BREACHED, PENDING
    calendar_type: str
    created_at: str
    completed_at: Optional[str] = None

class ResolutionModel(BaseModel):
    resolution_id: str
    ticket_id: str
    resolved_by_agent_id: str
    resolution_type: str
    root_cause_category: str
    notes: str
    customer_satisfaction_score: Optional[int] = None
    csat_feedback: Optional[str] = None
    resolved_at: str

class TicketModel(BaseModel):
    ticket_id: str
    customer_id: str
    channel_id: str
    intent_id: str
    language_code: str
    urgency: str
    priority_score: float
    assigned_agent_id: Optional[str] = None
    queue_id: str
    status: str
    created_at: str
    first_responded_at: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    is_reopened: bool = False
    reopen_count: int = 0
    transfer_count: int = 0
    escalation_level: int = 0
    anomaly_flag: Optional[str] = None

class GroundTruthAnomalyModel(BaseModel):
    anomaly_id: str
    ticket_id: str
    issue_type: str  # CAPACITY_EXCEEDED, CALENDAR_IGNORED, HISTORY_LOST, TRANSFER_LOOP, SAFETY_OVERRIDE_VIOLATION
    severity: str    # HIGH, CRITICAL, MEDIUM
    entity_id: str
    description: str
    expected_behavior: str
    actual_behavior: str
    root_cause: str
    suggested_remediation: str
    timestamp: str

class RoutingRequest(BaseModel):
    channel_id: str
    customer_id: str
    intent_id: str
    language_code: str
    initial_message: str
    urgency_override: Optional[str] = None

class RoutingDecisionResponse(BaseModel):
    ticket: TicketModel
    assignment_event: AssignmentEventModel
    sla_event: SLAEventModel
    routing_reasoning: Dict[str, Any]

class TicketDetailResponse(BaseModel):
    ticket: TicketModel
    customer: Optional[CustomerModel] = None
    agent: Optional[AgentModel] = None
    channel: Optional[ChannelModel] = None
    intent: Optional[IntentModel] = None
    messages: List[MessageModel] = []
    assignment_history: List[AssignmentEventModel] = []
    sla_event: Optional[SLAEventModel] = None
    resolution: Optional[ResolutionModel] = None
    anomaly: Optional[GroundTruthAnomalyModel] = None

class ActionRequest(BaseModel):
    agent_id: Optional[str] = None
    target_queue_id: Optional[str] = None
    target_agent_id: Optional[str] = None
    reason: Optional[str] = "Manual operator intervention"
    notes: Optional[str] = "Resolved successfully"
    csat_score: Optional[int] = 5
    csat_feedback: Optional[str] = "Great service"

class DatasetGenerationConfig(BaseModel):
    scale: str = "starter"  # "starter" (1,000 tickets) or "full" (30,000 tickets)
    seed: int = 20261022
    inject_anomalies: bool = True
