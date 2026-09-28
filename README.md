# HackwithHyderabad Agent

> **HackwithHyderabad 3.0 — AI Agents That Learn Using Hindsight**

---

## Current Goal (Part 0)

Establish the project foundation and development environment.
No agent, LLM, or Hindsight logic is implemented yet.

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

Only the **FastAPI Backend** layer is active in Part 0.

---

## Folder Structure

```
hackathon-agent/
├── frontend/          ← Vite + React (Part 0: status page only)
├── backend/
│   ├── api/           ← FastAPI route modules
│   ├── agent/         ← Agent core (future)
│   ├── memory/        ← Hindsight memory (future)
│   ├── tools/         ← Tool / function calling (future)
│   └── data/
│       └── sample_data/
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
| 1    | LLM service integration                   | 🔜 Pending  |
| 2    | Hindsight memory                          | 🔜 Pending  |
| 3    | Agent core                                | 🔜 Pending  |
| 4    | Tool / function calling                   | 🔜 Pending  |
| 5    | PS-specific functionality                 | 🔜 Pending  |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in values when needed:

```bash
cp .env.example .env
```

> **Never commit `.env` to source control.**
