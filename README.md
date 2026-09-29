# RECALL — AI-Powered Incident Response Agent

> AI agents that learn from previous incidents using Hindsight long-term memory.

---

## Project Overview

**RECALL** is an AI-powered incident-response agent that uses Hindsight long-term memory to turn resolved incidents into reusable operational knowledge.

The core idea is simple:

```
Incident -> Hindsight RECALL -> Agent Reasoning -> Response -> Hindsight RETAIN
```

When a new alert arrives, RECALL retrieves historical context about similar past incidents from Hindsight before the LLM reasons about the problem. Once an incident is resolved, the resolution — including what worked and what did not — is written back into Hindsight (RETAIN) so that future incidents can benefit from it. The system also supports REFLECT, which synthesises patterns and insights across many past incidents.

Previous incident experience becomes directly useful the next time a similar alert fires.

### Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite 8 |
| Backend | FastAPI + Python |
| LLM Provider | Groq (`groq` SDK, async) |
| LLM Model | `llama-3.3-70b-versatile` (configurable via `LLM_MODEL`) |
| Long-term Memory | Hindsight (`hindsight-client` SDK) |
| API | REST / JSON |
| Dependency loading | `python-dotenv` |

---

## Project Progress

### Core Foundation

- [x] Part 0 — Project Foundation
- [x] Part 1 — LLM API Layer
- [x] Part 2 — Hindsight Memory
- [x] Part 3 — Agent Core
- [x] Part 4 — Tool Framework
- [x] Part 5 — FastAPI Agent API
- [x] Part 6 — React UI
- [x] Part 7 — Hindsight Memory Visualization

### Incident Response System

- [x] Part 9 — Incident-response foundation
- [x] F1 — Alert Intake & Normalization
- [x] F2 — Hindsight Recall Planner
- [x] F3 — Evidence-Cited Diagnosis
- [x] F4 — Known-Bad Fix Avoidance
- [x] F5 — Outdated-Fix Detection
- [x] F6 — Engineer Feedback Loop
- [x] F7 — Incident Closure & Memory Write-Back
- [x] F8 — Pattern Digest / Reflect
- [x] F9 — Memory Inspector
- [x] F10 — Split-Screen Control Comparison
- [x] F11 — Learning Scoreboard / Evaluation
- [x] F12 — Synthetic Incident Generator / Seeder
- [x] F13 — Resilience (Hindsight health probe & graceful degradation)
- [x] F14 — Redaction / Safety

---

## Feature Status Table

| ID | Feature | Status | Implementation |
|----|---------|--------|----------------|
| F1 | Alert Intake & Normalization | Complete | `incident/normalizer.py` — deterministic signature generation, severity inference, log trimming |
| F2 | Hindsight Recall Planner | Complete | `incident/recall_planner.py` — multi-query targeted recall from Hindsight |
| F3 | Evidence-Cited Diagnosis | Complete | `incident/diagnosis.py` — LLM diagnosis grounded in recalled memories |
| F4 | Known-Bad Fix Avoidance | Complete | `incident/fix_analyzer.py` — deterministic scan of recalled memories for failed fixes |
| F5 | Outdated-Fix Detection | Complete | `incident/stale_detector.py` — version and environment staleness checks |
| F6 | Engineer Feedback Loop | Complete | `incident/feedback.py` + `POST /api/alerts/incidents/{id}/feedback` |
| F7 | Incident Closure & Memory Write-Back | Complete | `incident/closure.py` + `POST /api/alerts/incidents/{id}/close` then Hindsight RETAIN |
| F8 | Pattern Digest / Reflect | Complete | `incident/patterns.py` + `GET /api/alerts/patterns` + `PatternDigestView` (frontend) |
| F9 | Memory Inspector | Complete | `incident/memory_inspector.py` + `GET /api/alerts/memories` + `MemoryInspectorView` (frontend) |
| F10 | Split-Screen Control Comparison | Complete | `incident/comparator.py` + `POST /api/alerts/compare` + `ControlComparisonView` (frontend) |
| F11 | Learning Scoreboard / Evaluation | Complete | `incident/evaluator.py` + `POST /api/alerts/evaluate` + `EvaluationScoreboardView` (frontend) |
| F12 | Synthetic Incident Generator / Seeder | Complete | `incident/generator.py` + `POST /api/alerts/seed` + `SyntheticSeederView` (frontend) |
| F13 | Resilience | Complete | `incident/resilience.py` + `GET /api/alerts/resilience` + `ResilienceHeader` (frontend) |
| F14 | Redaction / Safety | Complete | `incident/redaction.py` — applied inside normalizer before any Hindsight RETAIN |

---

## Architecture

### System Overview

```
User
 |
 v
React Frontend  (Vite, port 5173)
 |
 v
FastAPI Backend  (Uvicorn, port 8000)
 |-- /api/health              <- liveness check
 |-- /api/agent/*             <- generic chat agent
 +-- /api/alerts/*            <- incident response system
        |
        v
IncidentResponseService / Agent
 |-- LLMService (Groq, async)
 |-- HindsightMemory
 |     |-- RECALL  : retrieve relevant historical context
 |     |-- RETAIN  : store new knowledge after resolution
 |     +-- REFLECT : synthesise patterns across many memories (F8)
 +-- Tool Framework (registry, executor, calculator)
        |
        v
Incident Response Pipeline
  F14 Redact -> F1 Normalize -> F13 Health Probe
  -> F2 Recall Planner -> F3 Diagnose
  -> F4 Known-Bad Fix Analysis -> F5 Stale-Fix Detection
  -> F6 Engineer Feedback -> F7 Closure + Hindsight RETAIN
```

### Hindsight Memory Operations

| Operation | When Used |
|-----------|-----------|
| **RECALL** | Before every diagnosis — retrieves historical incident context matching the current alert |
| **RETAIN** | After incident closure (F7) and engineer feedback (F6) — writes the resolution into Hindsight |
| **REFLECT** | F8 Pattern Digest — synthesises recurring patterns across all stored memories |

### Key Design Decision

The generic `Agent` (chat) and the `IncidentResponseService` (incident pipeline) share the same `LLMService` and `HindsightMemory` instances, injected at startup via FastAPI's lifespan context. They are completely independent — incident logic never touches `Agent.run()`.

---

## Folder Structure

```
hackathon-agent/
|-- .env.example               <- Environment variable template (copy -> .env)
|-- .gitignore
|-- README.md
|-- requirements.txt           <- Python dependencies
|-- test_api.py                <- Root-level quick API test
|-- test_get_mem.py            <- Root-level memory retrieval test
|
|-- backend/
|   |-- __init__.py
|   |-- config.py              <- Central env-var config (LLM + Hindsight)
|   |-- main.py                <- FastAPI app entry point, lifespan startup
|   |
|   |-- agent/
|   |   |-- agent.py           <- Generic Agent Core (recall -> LLM -> retain)
|   |   |-- llm.py             <- Provider-agnostic LLM service (Groq async)
|   |   +-- prompts.py         <- System prompt and prompt builder
|   |
|   |-- api/
|   |   |-- routes.py          <- GET /api/health
|   |   |-- agent_routes.py    <- POST /api/agent/chat, GET /api/agent/memory/{user_id}
|   |   +-- incident_routes.py <- All /api/alerts/* incident endpoints
|   |
|   |-- incident/
|   |   |-- models.py          <- Pydantic models for the entire incident domain
|   |   |-- service.py         <- IncidentResponseService orchestrator
|   |   |-- normalizer.py      <- F1 alert normalization + signature generation
|   |   |-- redaction.py       <- F14 secrets redaction before Hindsight RETAIN
|   |   |-- recall_planner.py  <- F2 multi-query Hindsight recall planner
|   |   |-- diagnosis.py       <- F3 evidence-cited LLM diagnosis
|   |   |-- fix_analyzer.py    <- F4 known-bad fix detection from memory
|   |   |-- stale_detector.py  <- F5 outdated fix detection by version/env
|   |   |-- feedback.py        <- F6 engineer feedback capture + Hindsight retain
|   |   |-- closure.py         <- F7 incident closure + resolution write-back
|   |   |-- patterns.py        <- F8 pattern digest via Hindsight recall
|   |   |-- memory_inspector.py <- F9 raw Hindsight memory inspection
|   |   |-- comparator.py      <- F10 control vs Hindsight split-screen comparison
|   |   |-- evaluator.py       <- F11 learning scoreboard benchmark harness
|   |   |-- generator.py       <- F12 synthetic incident seeder
|   |   +-- resilience.py      <- F13 Hindsight health probe + graceful degradation
|   |
|   |-- memory/
|   |   +-- hindsight.py       <- HindsightMemory wrapper (remember/recall/reflect/ensure_bank)
|   |
|   |-- tools/
|   |   |-- base.py            <- Abstract Tool base class
|   |   |-- registry.py        <- ToolRegistry (register, get, list)
|   |   |-- executor.py        <- ToolExecutor (execute with error handling)
|   |   +-- builtins.py        <- CalculatorTool (add/subtract/multiply/divide)
|   |
|   +-- data/
|       +-- sample_data/       <- Sample data directory
|
|-- frontend/
|   |-- index.html
|   |-- package.json           <- React 19 + Vite 8 dependencies
|   |-- vite.config.js
|   +-- src/
|       |-- main.jsx
|       |-- App.jsx            <- Root component, tab routing, session management
|       |-- App.css
|       |-- index.css
|       |-- services/
|       |   +-- api.js         <- All API calls for chat + all F1-F13 incident endpoints
|       +-- components/
|           |-- Sidebar.jsx / .css           <- Navigation sidebar with all tabs
|           |-- TopHeader.jsx / .css         <- Header bar
|           |-- ResilienceHeader.jsx / .css  <- F13 Hindsight connection status indicator
|           |-- ChatWindow.jsx / .css        <- Agent chat message list
|           |-- ChatMessage.jsx / .css       <- Individual message bubble
|           |-- MessageInput.jsx / .css      <- Chat input with send button
|           |-- MemoryPanel.jsx / .css       <- Right sidebar: Hindsight memory viewer
|           |-- IncidentDashboard.jsx / .css <- Main incident response UI (F1-F7)
|           |-- MemoryInspectorView.jsx/.css <- F9 raw memory inspector
|           |-- PatternDigestView.jsx / .css <- F8 pattern digest view
|           |-- ControlComparisonView.jsx/.css <- F10 split-screen comparison
|           |-- EvaluationScoreboardView.jsx/.css <- F11 learning scoreboard
|           |-- SyntheticSeederView.jsx / .css <- F12 synthetic seeder
|           |-- WelcomeState.jsx / .css      <- Empty state for chat
|           |-- Header.jsx / .css            <- Sub-header component
|           +-- Icons.jsx                   <- SVG icon library
|
+-- scripts/
    |-- test_llm.py                    <- LLM smoke test (Groq)
    |-- test_hindsight.py              <- Hindsight store + recall smoke test
    |-- test_agent.py                  <- Agent Core interaction test
    |-- test_tools.py                  <- Tool framework unit tests
    |-- test_api.py                    <- API endpoint integration test
    |-- test_incident_slice1.py        <- F1/F14/F2/F3 pipeline test
    |-- test_incident_slice2.py        <- F4/F5/F6/F7 pipeline test
    +-- test_incident_learning_loop.py <- End-to-end learning loop verification
```

---

## Setup & Running

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- A running Hindsight instance
- A Groq API key (from [console.groq.com](https://console.groq.com))

### Backend

```bash
# From the project root
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

### Environment Configuration

Copy `.env.example` to `.env` and fill in real values:

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Edit `.env`:

```env
# LLM
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=<your key from console.groq.com>

# Hindsight memory service
HINDSIGHT_URL=http://your-hindsight-url:8888
HINDSIGHT_API_KEY=your-hindsight-api-key-here
```

> **Never commit `.env` to source control.** It is already in `.gitignore`.

### Running

**Backend** (with venv active, from project root):

```bash
uvicorn backend.main:app --reload --port 8000
```

**Hindsight** (if running locally via the installed CLI):

```bash
.\venv\Scripts\hindsight-api.exe
```

**Frontend** (from the `frontend/` directory):

```bash
npm run dev
# Opens at http://localhost:5173
```

---

## API Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Liveness check |

### Agent Chat

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/agent/chat` | Send a message; returns LLM response + memory metadata |
| GET | `/api/agent/memory/{user_id}` | Retrieve all Hindsight memories for a user |

### Incident Response

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/alerts/diagnose` | F1+F14+F2+F3+F4+F5 full diagnosis pipeline |
| GET | `/api/alerts/incidents` | List all diagnosed incidents (session-scoped) |
| GET | `/api/alerts/incidents/{id}` | Get a single incident by ID |
| POST | `/api/alerts/incidents/{id}/feedback` | F6 — submit engineer feedback |
| POST | `/api/alerts/incidents/{id}/close` | F7 — close incident + write-back to Hindsight |
| GET | `/api/alerts/patterns` | F8 — pattern digest from Hindsight |
| GET | `/api/alerts/memories` | F9 — inspect raw Hindsight incident memories |
| POST | `/api/alerts/compare` | F10 — control vs Hindsight split-screen comparison |
| POST | `/api/alerts/evaluate` | F11 — run learning evaluation benchmark |
| POST | `/api/alerts/seed` | F12 — seed synthetic historical incidents |
| GET | `/api/alerts/resilience` | F13 — Hindsight health probe status |

---

## Part 0 — Project Foundation

Established the full project structure:

- FastAPI application with CORS middleware configured for the Vite dev server (port 5173)
- Lifespan context manager for service initialization and graceful shutdown
- Central `config.py` loading all configuration from environment variables via `python-dotenv`
- `GET /api/health` liveness endpoint
- React + Vite frontend scaffold

---

## Part 1 — LLM API Layer

`backend/agent/llm.py` provides a **provider-agnostic LLM service**.

```
LLMService.generate(system_prompt, user_prompt)   <- single async public method
      |
      v
_call_groq_async(...)     <- Groq async provider (AsyncGroq)
      |
      v
Groq API (llama-3.3-70b-versatile)
```

- Provider abstraction: adding a new provider requires one function and one registry entry — `Agent` is untouched
- Groq SDK (`groq`) with `AsyncGroq` for async generation
- Synchronous `generate_sync` retained for smoke tests
- `LLMConfigError` raised on missing `LLM_API_KEY` or unknown provider
- `LLMProviderError` raised on empty or failed API response
- Model and provider are fully configurable via `LLM_MODEL` and `LLM_PROVIDER` in `.env`

**Smoke test:**

```bash
python scripts/test_llm.py
```

---

## Part 2 — Hindsight Memory

`backend/memory/hindsight.py` wraps the `hindsight-client` SDK with a clean async interface.

```
Agent / IncidentResponseService
      |
      v
HindsightMemory
 |-- remember(bank_id, content)      <- aretain: write a memory
 |-- recall(bank_id, query)          <- arecall: retrieve relevant memories
 |-- reflect(bank_id, query, budget) <- areflect: synthesise insight
 |-- ensure_bank(bank_id)            <- create bank if it does not exist (404-aware)
 |-- get_memories(bank_id)           <- alist_memories: list all memory units
 +-- close()                         <- aclose / close: release client resources
      |
      v
Hindsight Server (HINDSIGHT_URL)
```

- `HINDSIGHT_URL` and optional `HINDSIGHT_API_KEY` configured in `.env` / `config.py`
- `HindsightConfigError` raised on missing URL or failed client initialization
- `HindsightMemoryError` raised on any operation failure
- Bank creation is automatic via `ensure_bank` — 404 responses trigger `acreate_bank`
- Client is gracefully closed at application shutdown via the lifespan handler

**Smoke test:**

```bash
python scripts/test_hindsight.py
```

---

## Part 3 — Agent Core

`backend/agent/agent.py` implements the generic conversational agent loop.

```
User message (user_id + message)
      |
      v
1. Validate input
      |
      v
2. ensure_bank(user_id) -> HindsightMemory
      |
      v
3. recall(bank_id=user_id, query=message) -> memory_context
      |
      v
4. build_agent_prompt(memory_context, user_message)
      |
      v
5. LLMService.generate(system_prompt, user_prompt) -> answer
      |
      v
6. remember(bank_id=user_id, content="User asked: ... / Assistant: ...")
      |
      v
7. Return {response, memory_used, memory_context}
```

Memory context and the current user message are kept conceptually separate in the prompt builder: historical context is labelled and presented before the live user question.

---

## Part 4 — Tool Framework

`backend/tools/` provides an extensible tool dispatch system.

| File | Purpose |
|------|---------|
| `base.py` | Abstract `Tool` ABC with `name`, `description`, `input_schema`, `execute` |
| `registry.py` | `ToolRegistry` — register, get, list; raises on duplicates and unknown tools |
| `executor.py` | `ToolExecutor` — dispatches calls, handles `ValueError` and unknown tools |
| `builtins.py` | `CalculatorTool` — add / subtract / multiply / divide; raises on divide-by-zero |

Error handling covers: duplicate registration, unknown tool names, invalid arguments, and divide-by-zero.

---

## Part 5 — FastAPI Agent API

Two route modules exposed under `/api/agent`:

- `POST /api/agent/chat` — calls `Agent.run(user_id, message)`, returns `{response, memory_used, memory_context}`
- `GET /api/agent/memory/{user_id}` — calls `memory.get_memories(user_id)`, returns formatted memory list

Both endpoints return `503` if the agent or memory service failed to initialize at startup (e.g., missing API keys).

---

## Part 6 — React UI

The frontend is a single-page React 19 application served by Vite.

**Tab navigation (Sidebar):**

| Tab | View |
|-----|------|
| Chat | Generic agent chat with Hindsight memory panel |
| Incidents | Full incident response dashboard (F1-F7) |
| Memory Inspector | F9 — raw Hindsight memory browser |
| Patterns | F8 — pattern digest viewer |
| Compare | F10 — control vs Hindsight split-screen |
| Scoreboard | F11 — learning evaluation scoreboard |
| Seed Data | F12 — synthetic incident seeder |

**Key features:**

- Persistent user/session identifier stored in `localStorage` (`hackathon_user_id`) — auto-generated on first visit
- Resilience status polled every 30 seconds via `GET /api/alerts/resilience`; displayed in `ResilienceHeader`
- Right-panel `MemoryPanel` shows live Hindsight memories for the current user after every chat message
- All API calls centralized in `src/services/api.js`; errors surface with status codes for targeted handling

---

## Part 7 — Hindsight Memory Visualization

The `MemoryPanel` component displays the agent's per-user Hindsight memories in the right sidebar, updated automatically after each chat interaction.

For the incident system, `MemoryInspectorView` provides a dedicated view that calls `GET /api/alerts/memories` and presents the raw structured incident memories stored in Hindsight, with optional service-name filtering.

---

## Incident Response Features

### F1 — Alert Intake & Normalization

**Purpose:** Convert free-text alerts (copy-pasted from PagerDuty, Grafana, Slack, log outputs) into a structured `NormalizedAlert` with a stable, reproducible signature.

**Implementation:** `backend/incident/normalizer.py`

- Pure, deterministic — no LLM calls, no Hindsight calls
- Strips timestamps, pod suffixes, IP addresses, and numeric IDs before generating the `error_signature` so the same underlying error always produces the same signature regardless of when or where it occurred
- Severity inferred from keyword patterns (critical -> CRITICAL, error/exception -> HIGH, warning/timeout -> MEDIUM, info -> LOW)
- Service name inferred from a known-services dictionary if not explicitly provided
- Log trimming: returns up to 20 lines centred around the first high-scoring error line
- F14 redaction is applied inside the normalizer before any further processing

**Status:** Complete

---

### F2 — Hindsight Recall Planner

**Purpose:** Generate targeted recall queries and retrieve relevant historical incident context from Hindsight before diagnosis.

**Implementation:** `backend/incident/recall_planner.py`

- Produces multiple query strategies (by error signature, by service, general incident patterns)
- Returns a `RecallPlannerResult` with `memories`, `queries`, and `used_memory` flag
- `used_memory` is `False` when Hindsight is unavailable or returns no results

**Status:** Complete

---

### F3 — Evidence-Cited Diagnosis

**Purpose:** Produce an LLM-generated diagnosis that is explicitly grounded in the recalled Hindsight memories, not in the model's unverified general knowledge.

**Implementation:** `backend/incident/diagnosis.py`

- System prompt instructs the LLM to cite evidence from recalled memories
- Returns `DiagnosisResult` with `incident_id`, `root_cause`, `evidence_items`, `recommended_actions`, and optional `memory_warning`
- If no memory was recalled, a warning is included in the response

**Status:** Complete

---

### F4 — Known-Bad Fix Avoidance

**Purpose:** Scan recalled memories for fixes that were previously attempted and failed, and surface them so engineers are not misled into repeating them.

**Implementation:** `backend/incident/fix_analyzer.py`

- Fully deterministic — no LLM call
- Returns `FixAnalysisResult` with `known_bad_fixes` and `mixed_result_fixes`
- Integrated into `diagnose_alert` pipeline; results included in `DiagnoseResponse`

**Status:** Complete

---

### F5 — Outdated-Fix Detection

**Purpose:** Identify historical fixes that were valid in a previous version or environment but may no longer apply to the current deployment.

**Implementation:** `backend/incident/stale_detector.py`

- Compares service version and environment from the current alert against metadata in recalled memories
- Returns `StaleDetectionResult` with `assessments` for each recalled memory
- Accepts optional `service_version`, `environment`, and `deployment_id` from the diagnose request

**Status:** Complete

---

### F6 — Engineer Feedback Loop

**Purpose:** Allow engineers to mark a diagnosis as accepted, rejected, or corrected, and retain that feedback in Hindsight for future recall.

**Implementation:** `backend/incident/feedback.py` + `POST /api/alerts/incidents/{id}/feedback`

- Accepts `feedback_type` (accepted / rejected / corrected), `engineer_id`, `comment`, and optional `corrected_action`
- Feedback is retained in Hindsight (non-fatal — stored locally if Hindsight retain fails)
- Frontend: integrated in `IncidentDashboard`

**Status:** Complete

---

### F7 — Incident Closure & Memory Write-Back

**Purpose:** Close an incident and write a structured resolution memory into Hindsight so future incidents can recall it.

**Implementation:** `backend/incident/closure.py` + `POST /api/alerts/incidents/{id}/close`

- Accepts `final_diagnosis`, `resolution_action`, `outcome`, `resolution_success`, and `notes`
- F14 redaction is applied to all fields before Hindsight RETAIN
- Returns `ClosureResponse` with `memory_writeback.succeeded` and `memory_writeback.error` fields
- Idempotent — already-closed incidents return `already_closed` status
- Frontend: integrated in `IncidentDashboard`

**Status:** Complete

---

### F8 — Pattern Digest / Reflect

**Purpose:** Surface recurring incident patterns, root causes, successful resolutions, and known failed approaches across all historical incidents stored in Hindsight.

**Implementation:** `backend/incident/patterns.py` + `GET /api/alerts/patterns` + `PatternDigestView` (frontend)

- Uses Hindsight RECALL with a broad reflective query
- Parses structured memory blocks to extract recurring signatures, affected services, and resolution patterns
- Returns gracefully when bank is empty or Hindsight is unavailable
- Frontend view allows optional service-name filtering

**Status:** Complete (backend + frontend)

---

### F9 — Memory Inspector

**Purpose:** Allow engineers to inspect the raw structured memories stored in Hindsight's incident bank.

**Implementation:** `backend/incident/memory_inspector.py` + `GET /api/alerts/memories` + `MemoryInspectorView` (frontend)

- Retrieves and parses real Hindsight memories for the `incidents` bank
- Extracts context type (`incident_resolution` vs `general_memory`) and service from memory content
- Supports optional service-name filtering
- Frontend view displays memories with content, type, and service metadata

**Status:** Complete (backend + frontend)

---

### F10 — Split-Screen Control Comparison

**Purpose:** Run the same alert through two agents side-by-side — a baseline agent with no memory and a Hindsight-enabled agent — to demonstrate the value of historical context.

**Implementation:** `backend/incident/comparator.py` + `POST /api/alerts/compare` + `ControlComparisonView` (frontend)

- Hindsight agent runs the full F1+F2+F3+F4+F5 pipeline
- Control agent runs F1+F3 with an empty recall (no memory)
- Returns both diagnoses for direct comparison

**Status:** Complete (backend + frontend)

---

### F11 — Learning Scoreboard / Evaluation

**Purpose:** Quantitatively benchmark the Hindsight-enabled agent against a no-memory baseline across a fixed set of representative incident scenarios.

**Implementation:** `backend/incident/evaluator.py` + `POST /api/alerts/evaluate` + `EvaluationScoreboardView` (frontend)

- Five benchmark cases covering: connection pool exhaustion, outdated version fix, failed runbook restart, DB query timeout, configuration drift
- Scores four dimensions: evidence availability, known-bad fix avoidance, stale-fix detection, resolution retrieval
- Returns per-case detail and aggregate scores for both baseline and Hindsight agent

**Status:** Complete (backend + frontend)

---

### F12 — Synthetic Incident Generator / Seeder

**Purpose:** Seed Hindsight with realistic historical incident memories to enable instant demonstration of recall, known-bad fix detection, and pattern digests.

**Implementation:** `backend/incident/generator.py` + `POST /api/alerts/seed` + `SyntheticSeederView` (frontend)

- Five pre-built synthetic incidents: payments-api pool exhaustion, auth-service OOMKilled, orders-service DB timeout, notification-service Kafka failure, stale version fix
- Each memory includes structured fields: service, error signature, root cause, resolution action, failed fixes, and engineer feedback
- F14 redaction applied before every RETAIN call
- Returns retained/failed counts and per-item error details

**Status:** Complete (backend + frontend)

---

### F13 — Resilience

**Purpose:** Provide a health probe for Hindsight connectivity and enable graceful degradation throughout the incident pipeline when Hindsight is unavailable.

**Implementation:** `backend/incident/resilience.py` + `GET /api/alerts/resilience` + `ResilienceHeader` (frontend)

- `is_hindsight_available()` used inside every `diagnose_alert` call to set no-memory mode
- `get_resilience_status()` returns `hindsight_connected`, `status` (online/degraded), and `fallback_active`
- Frontend `ResilienceHeader` polls every 30 seconds and displays connection state
- Diagnosis proceeds with a `memory_warning` if Hindsight is unavailable

**Status:** Complete (backend + frontend)

---

### F14 — Redaction / Safety

**Purpose:** Ensure that API keys, passwords, email addresses, bearer tokens, and UUID-shaped customer identifiers are never stored in Hindsight.

**Implementation:** `backend/incident/redaction.py`

Detected and replaced patterns:

| Pattern | Placeholder |
|---------|-------------|
| Bearer tokens | `<REDACTED_TOKEN>` |
| API keys / auth tokens (key=value) | `<REDACTED_TOKEN>` |
| Passwords (key=value and URL-embedded) | `<REDACTED_PASSWORD>` |
| Email addresses | `<REDACTED_EMAIL>` |
| IPv4 addresses (when `redact_ips=True`) | `<REDACTED_IP>` |
| UUID-shaped identifiers (when `redact_uuids=True`) | `<REDACTED_ID>` |

Applied in two places:

1. Inside `normalize_alert` (F1) — before the alert is processed
2. Inside `generator.py` (F12) — before synthetic memories are retained

Only redaction counts are logged; original values are never logged.

**Status:** Complete

---

## Learning Loop

RECALL's learning loop turns each resolved incident into knowledge that benefits future incidents:

```
Incident A fires
      |
      v
F1 Normalize -> F2 Recall (finds no prior history) -> F3 Diagnose (no memory context)
      |
      v
Engineer reviews diagnosis
      |
      v
F6 Feedback: engineer marks action as "corrected", provides the real fix
      |
      v
F7 Close Incident A: resolution written to Hindsight via RETAIN
      |
      v
Historical experience stored in Hindsight bank "incidents"
      |
      v
Incident B fires (same service, similar error)
      |
      v
F2 Recall: Hindsight RECALL retrieves Incident A's resolution
      |
      v
F3 Diagnosis now has evidence: failed fix, correct resolution action
      |
      v
F4 Known-Bad Fix Avoidance: previous failed runbook surfaces as warning
      |
      v
Better-informed, evidence-grounded diagnosis for Incident B
```

The repository includes `scripts/test_incident_learning_loop.py`, a full end-to-end test that verifies this loop against a live backend and Hindsight instance (Steps 1-7, covering diagnose -> feedback -> close -> retain -> diagnose -> recall verification -> F4/F5 evidence checks).

> **Note on rate limiting:** The learning loop test includes deliberate delays between the Hindsight RETAIN and subsequent RECALL operations. This is because Hindsight uses an external LLM provider (Groq) internally for memory processing, and that provider's per-minute token quota (TPM) can be hit during rapid sequential operations in testing. This is an external provider constraint, not a bug in RECALL. The test detects 429 / rate-limit errors and exits cleanly with a warning rather than a false failure.

---

## Testing & Verification

All tests live in `scripts/`. Run from the project root with the venv active.

| Test File | Purpose | Dependencies |
|-----------|---------|-------------|
| `scripts/test_llm.py` | LLM smoke test — sends a prompt to Groq, checks response | `LLM_API_KEY` set |
| `scripts/test_hindsight.py` | Hindsight store + recall smoke test | `HINDSIGHT_URL` set |
| `scripts/test_agent.py` | Agent Core interaction test | Both LLM + Hindsight |
| `scripts/test_tools.py` | Tool framework unit tests — all paths including error cases | None (pure) |
| `scripts/test_api.py` | API integration test — health + agent endpoints | Backend running |
| `scripts/test_incident_slice1.py` | F1/F14/F2/F3 pipeline test | Both LLM + Hindsight |
| `scripts/test_incident_slice2.py` | F4/F5/F6/F7 pipeline test | Both LLM + Hindsight |
| `scripts/test_incident_learning_loop.py` | End-to-end learning loop (Incident A -> RETAIN -> Incident B -> RECALL) | Backend + Hindsight running |

Tests that require no external services (e.g., `test_tools.py`) run without any environment setup.

Tests that require LLM or Hindsight skip gracefully with instructions when the required configuration is not present.

---

## Known Limitations

### External LLM Provider Rate Limiting (Groq TPM Quota)

Hindsight processes memories using an external LLM provider internally. When running multiple back-to-back memory operations in quick succession (as in the learning loop test), Groq's per-minute token quota (TPM) can be exhausted. This manifests as a 429 Too Many Requests error during RETAIN or RECALL operations.

This is a constraint of the external provider, not a defect in RECALL or Hindsight. In production, normal incident cadence is spread over time and does not hit this limit. In testing, delays between operations mitigate it.

The `IncidentResponseService` handles Hindsight failures non-fatally wherever possible:

- If Hindsight is unavailable at diagnosis time, the pipeline continues in no-memory mode with a `memory_warning` in the response
- If Hindsight RETAIN fails at incident closure, the `ClosureResponse` reports `memory_writeback.succeeded=False` with the error detail
- If Hindsight RETAIN fails for engineer feedback, the feedback is stored locally and a warning is appended to the response message

The F13 Resilience module provides real-time connectivity status and the `ResilienceHeader` component surfaces it in the UI.

### In-Memory Incident Store

The `IncidentResponseService` uses a simple in-process Python dict as its incident store. Incidents are lost on backend restart. This is by design for the current prototype phase.

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | No (default: `groq`) | LLM provider identifier |
| `LLM_MODEL` | No (default: `llama-3.3-70b-versatile`) | Model name passed to the provider |
| `LLM_API_KEY` | **Yes** | API key for the LLM provider |
| `HINDSIGHT_URL` | **Yes** | Base URL of the Hindsight server (e.g. `http://localhost:8888`) |
| `HINDSIGHT_API_KEY` | No | API key for Hindsight (if required by your instance) |
