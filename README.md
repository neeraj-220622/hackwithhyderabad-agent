# HackwithHyderabad Agent

> **HackwithHyderabad 3.0 — AI Agents That Learn Using Hindsight**

---

## Completed

- **Part 0** — Project foundation, FastAPI skeleton, health endpoint, React status page.
- **Part 1** — Provider-agnostic LLM service (Groq, configurable model).

---

## Architecture (Planned)

```
React Frontend
      ↓
FastAPI Backend
      ↓
Agent Core
      ↓
 ┌────┼────┐
 ↓    ↓    ↓
LLM  Hindsight  Tools
                  ↓
           PS-specific logic
```

The **LLM service** (Part 1) sits inside the Agent layer. The Agent Core will call `LLMService` in Part 3 without knowing which provider is used.

---

## Folder Structure

```
hackathon-agent/
├── frontend/              ← Vite + React (status page)
├── backend/
│   ├── api/
│   │   └── routes.py      ← FastAPI routes (GET /api/health)
│   ├── agent/
│   │   └── llm.py         ← LLMService (Part 1) ✅
│   ├── memory/            ← Hindsight memory (future)
│   ├── tools/             ← Tool / function calling (future)
│   ├── data/sample_data/
│   ├── config.py          ← Central env-var config (Part 1) ✅
│   └── main.py            ← FastAPI app entry point
├── scripts/
│   └── test_llm.py        ← LLM smoke test (Part 1) ✅
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Backend Setup

```bash
# From the project root
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

## Frontend Setup

```bash
cd frontend
npm install
```

---

## How to Run

### Backend

```bash
# From the project root (with venv active)
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm run dev
# Opens at http://localhost:5173
```

---

## Current API Endpoints

| Method | Path         | Description       |
|--------|--------------|-------------------|
| GET    | /api/health  | Liveness check    |

**Example response:**

```json
{
  "status": "ok",
  "service": "hackwithhyderabad-agent"
}
```

---

## Development Strategy

The application is being built incrementally. Domain-specific functionality will be added after the final problem statement is selected.

| Part | Scope                                     | Status      |
|------|-------------------------------------------|-------------|
| 0    | Foundation, project structure, health API | ✅ Complete |
| 1    | LLM service integration (Groq)            | ✅ Complete |
| 2    | Hindsight memory                          | 🔜 Pending  |
| 3    | Agent core                                | 🔜 Pending  |
| 4    | Tool / function calling                   | 🔜 Pending  |
| 5    | PS-specific functionality                 | 🔜 Pending  |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in real values:

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Then edit `.env`:

```
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=<your key from console.groq.com>
```

> **Never commit `.env` to source control.** It is already in `.gitignore`.

---

## Part 1 — LLM Layer

### Overview

`backend/agent/llm.py` provides a **provider-agnostic LLM service**.
The rest of the application only imports `LLMService` — Groq SDK details are hidden.

```
Future Agent Core
      ↓
 LLMService.generate(prompt)   ← single public method
      ↓
 _call_groq(...)               ← provider implementation
      ↓
 Groq API
```

Adding a new provider (e.g. OpenAI) requires adding one function and one line in `_PROVIDERS` — the Agent Core is unchanged.

### Current provider: Groq

- SDK: `groq` (OpenAI-compatible)
- Default model: `llama-3.3-70b-versatile` (configurable via `LLM_MODEL`)
- API key: stored in `.env` as `LLM_API_KEY` — **never hard-coded**

### Configuration

All LLM settings live in `backend/config.py`, loaded via `python-dotenv`.

### Smoke test

```bash
# From project root, with venv active
python scripts/test_llm.py
```

If `LLM_API_KEY` is not set, the script prints setup instructions and exits cleanly.
