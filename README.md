# OmniRoute: Intelligent Omnichannel Case Routing & SLA Engine

**Statement:**
> *Route email/chat/phone cases by intent, urgency, language, skill and agent capacity while tracking SLA.*

OmniRoute is a production-grade fullstack application designed to solve complex omnichannel customer support routing challenges. It balances skills, shift times, and agent concurrency limits, tracks SLA deadlines across business and 24x7 calendars, preserves an immutable audit trail of state changes, and exposes an anomaly detector for negative edge cases.

---

## 🚀 Key Highlights & Architecture

- **Frontend:** React 18 SPA (Vite + Tailwind CSS + Lucide Icons) featuring a live Decision Trace console, Case Explorer, Agent Matrix, Anomaly Auditor, Data Dictionary, and Integrity Runner.
- **Backend:** FastAPI (Python 3.14) with modular micro-architecture:
  - `router.py`: Real-time Algorithmic Routing Engine with safety policy guards.
  - `generator.py`: Deterministic synthetic generator with fixed seed parameterization (`20261022`).
  - `validator.py`: Comprehensive integrity and reproducibility test runner.
- **Database:** MongoDB (PyMongo) with automatic fallback to high-performance local document store for zero-friction local execution without external service dependencies.
- **Master Data & Deterministic IDs:**
  - `TKT-2026-000001` (Tickets)
  - `MSG-TKT-2026-000001-001` (Threaded Messages)
  - `AGT-000001` (Agents)
  - `ASN-TKT-2026-000001-001` (Immutable Assignment Events)
  - `SLA-TKT-2026-000001` (SLA Deadlines & Performance)
  - `RES-TKT-2026-000001` (Resolution & CSAT)

---

## 📊 Core Entities & Cardinality (13 Tables)

| Entity | Primary Key | Key Relationships | Description |
| :--- | :--- | :--- | :--- |
| **Customer** | `customer_id` (`CUST-000001`) | 1:N with `Ticket` | Customer identity, tier (Standard/Premium/Enterprise), preferred language |
| **Channel** | `channel_id` (`CH-EMAIL`, `CH-CHAT`, `CH-PHONE`) | 1:N with `Ticket` | Operating hours (Business vs 24x7), concurrency weight, target FRT/TTR |
| **Language** | `language_code` (`en`, `es`, `fr`, `de`, `zh`, `hi`) | 1:N with `Customer`, `Agent` | Recognized customer and agent fluency codes |
| **Skill** | `skill_id` (`SKL-BILLING`, `SKL-SECURITY`, ...) | N:M with `Agent` | Competencies required to resolve tickets across tiers 1-3 |
| **Queue** | `queue_id` (`QUE-BILLING`, `QUE-SECURITY`, ...) | 1:N with `Ticket` | Holding queues mapped to skills, max wait times, and escalation queues |
| **Intent** | `intent_id` (`INT-001` to `INT-007`) | 1:N with `Ticket` | Taxonomy of inquiries mapping to skills, default queues, base urgency |
| **PriorityRule** | `rule_id` (`RULE-001` to `RULE-009`) | N:1 with `Intent` | Matrix calculating urgency from tier + safety critical policy floors |
| **Agent** | `agent_id` (`AGT-000001` to `AGT-000100`) | 1:N with `AssignmentEvent` | Skills, languages, shift start/end hours, max concurrent capacity, load |
| **Ticket** | `ticket_id` (`TKT-2026-000001`) | 1:N `Message`, 1:N `Assignment` | Central case record with priority score, status lifecycle, SLA links |
| **Message** | `message_id` (`MSG-TKT-...-001`) | N:1 with `Ticket` | Threaded customer, agent, and system communications across channels |
| **AssignmentEvent**| `assignment_id` (`ASN-TKT-...-001`) | N:1 with `Ticket` | Immutable audit log of routing, transfers, escalations, and load |
| **SLAEvent** | `sla_id` (`SLA-TKT-...`) | 1:1 with `Ticket` | Target vs actual FRT/TTR, deadlines, calendar type, breach warning |
| **Resolution** | `resolution_id` (`RES-TKT-...`) | 1:1 with `Ticket` | Root-cause category, resolution notes, CSAT score (1-5) and feedback |

---

## 🎯 Required Edge Cases / Negative Scenarios

All 5 required edge cases are deterministically injected and tracked in `backend/data/ground_truth.json` and `ground_truth.csv` without feature leakage:

1. **`CAPACITY_EXCEEDED`**: Agent assigned beyond concurrency ceiling (e.g., load exceeding `max_concurrent_capacity`).
2. **`CALENDAR_IGNORED`**: SLA calculation applies 24x7 clock to a `BUSINESS_HOURS` email channel across weekends.
3. **`HISTORY_LOST`**: Reopened ticket loses historical messages or prior `AssignmentEvent` audit links in state transition.
4. **`TRANSFER_LOOP`**: Case enters an oscillating transfer loop between two agents (`AGT-A -> AGT-B -> AGT-A -> AGT-B`).
5. **`SAFETY_OVERRIDE_VIOLATION`**: Critical security or emergency intent (`INT-007`) downgraded to `LOW` urgency in violation of minimum safety policy floor.

---

## 🛠️ Step-by-Step Setup & How to Run

### 1. Prerequisites
- Python 3.10+ (Python 3.14 tested and supported)
- Node.js 18+ & npm
- (Optional) MongoDB daemon running on `localhost:27017` (auto-falls back to local DocumentStore if not running)

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies (already installed if in workspace)
pip install -r requirements.txt

# Run the test suite
python -m pytest tests/

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
# Or run from project root:
# python run_app.py
```
API Documentation will be live at: `http://127.0.0.1:8001/docs`

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install packages
npm install

# Build production bundle (served automatically by FastAPI at port 8001)
npm run build

# OR run Vite hot-reload development server (ensure backend is running on port 8001)
npm run dev
```
Development UI will be live at: `http://localhost:5173` (proxied to port 8001)
Production UI will be live at: `http://127.0.0.1:8001/`

---

## 🔬 Deterministic Reproducibility (Step 10)

To verify deterministic generation and checksum parity:
```bash
python -c "from app.services.validator import data_validator; print(data_validator.verify_reproducibility(seed=20261022))"
```
**Output:**
```json
{
  "reproducible": true,
  "seed": 20261022,
  "counts_match": true,
  "run_1_checksum": "e5467f979effe8d34e1ea82c619e8ba34098838eebffd6d4453aaa1f29a08411",
  "run_2_checksum": "e5467f979effe8d34e1ea82c619e8ba34098838eebffd6d4453aaa1f29a08411"
}
```

---

## 📦 Generated Dataset Files (`backend/data/`)
- `seed_manifest.json`: Scale, seed, row counts, and SHA-256 hash
- `data_dictionary.json`: Complete 13-entity schema specification
- `ground_truth.json` & `ground_truth.csv`: Isolated labeled negative scenarios
- `tickets.csv`, `customers.csv`, `channels.csv`, `messages.csv`, `agents.csv`, `assignment_events.csv`, `sla_events.csv`, `resolutions.csv`, `queues.csv`, `skills.csv`, `intents.csv`, `priority_rules.csv`, `languages.csv`
