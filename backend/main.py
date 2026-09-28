"""
HackwithHyderabad Agent — FastAPI Backend Entry Point
Part 0: Foundation only. No agent, LLM, or hindsight logic yet.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router

app = FastAPI(
    title="HackwithHyderabad Agent",
    description="Incremental AI agent backend for HackwithHyderabad 3.0.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server (port 5173) to reach the backend
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — add new route modules here as the project grows
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api")
