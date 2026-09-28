"""
API routes — Part 0.
Only the /health endpoint is implemented here.
Add new routers (agent, memory, tools …) as new include_router() calls in main.py.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check():
    """Liveness check — confirms the backend is running."""
    return {"status": "ok", "service": "hackwithhyderabad-agent"}
