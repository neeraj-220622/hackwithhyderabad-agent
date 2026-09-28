"""
backend/api/agent_routes.py
---------------------------
FastAPI routes for the Agent Core.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

class AgentChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="Unique identifier for the user.")
    message: str = Field(..., min_length=1, description="The user's message.")

class AgentChatResponse(BaseModel):
    response: str = Field(..., description="The assistant's generated response.")
    memory_used: bool = Field(..., description="Whether Hindsight memory was actively used.")
    memory_context: str = Field(..., description="The historical context that was recalled.")

@router.post("/chat", response_model=AgentChatResponse, summary="Agent Chat Endpoint")
async def chat_endpoint(request: Request, body: AgentChatRequest):
    """
    Process a user message using the Agent Core.
    Recalls Hindsight memory, generates an LLM response, and stores the interaction.
    """
    # Ensure inputs are stripped of whitespace
    user_id = body.user_id.strip()
    message = body.message.strip()

    if not user_id or not message:
        raise HTTPException(status_code=400, detail="user_id and message cannot be empty or whitespace only.")

    agent = getattr(request.app.state, "agent", None)
    if not agent:
        raise HTTPException(
            status_code=503, 
            detail="Agent Core is not available (LLM or Hindsight may be misconfigured)."
        )

    try:
        result = await agent.run(user_id=user_id, message=message)
        return AgentChatResponse(
            response=result["response"],
            memory_used=result["memory_used"],
            memory_context=result["memory_context"]
        )
    except Exception as exc:
        logger.error(f"Agent run failed: {exc}")
        error_msg = str(exc).lower()
        if "hindsight" in error_msg or "memory" in error_msg:
            raise HTTPException(status_code=503, detail="Hindsight memory service is currently unavailable.")
        
        # Generic fallback for LLM or unexpected errors
        raise HTTPException(status_code=500, detail="Internal server error during agent execution.")
