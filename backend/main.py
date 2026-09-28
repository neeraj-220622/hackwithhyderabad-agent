"""
HackwithHyderabad Agent — FastAPI Backend Entry Point
Part 0: Foundation only. No agent, LLM, or hindsight logic yet.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router
from backend.api.agent_routes import router as agent_router
from backend.agent.llm import LLMService, LLMConfigError
from backend.memory.hindsight import HindsightMemory, HindsightConfigError
from backend.agent.agent import Agent

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize core services at startup
    memory = None
    try:
        llm = LLMService()
        memory = HindsightMemory()
        app.state.agent = Agent(llm=llm, memory=memory)
        app.state.memory = memory  # Keep reference for cleanup
        logger.info("Agent Core initialized successfully.")
    except (LLMConfigError, HindsightConfigError) as e:
        logger.warning(f"Agent Core initialization skipped or failed: {e}")
        app.state.agent = None
        app.state.memory = None
    
    yield
    # Shutdown logic
    if app.state.memory:
        await app.state.memory.close()


app = FastAPI(
    title="HackwithHyderabad Agent",
    description="Incremental AI agent backend for HackwithHyderabad 3.0.",
    version="0.1.0",
    lifespan=lifespan,
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
app.include_router(agent_router, prefix="/api/agent", tags=["agent"])
