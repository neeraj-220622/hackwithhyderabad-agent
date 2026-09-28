"""
backend/agent/agent.py
----------------------
Generic Agent Core.

Integrates LLM Service and Hindsight Memory to process user messages,
retrieve context, generate answers, and store new memories.
"""

import logging

logger = logging.getLogger(__name__)

from backend.agent.prompts import SYSTEM_PROMPT, build_agent_prompt
from backend.agent.llm import LLMService, LLMProviderError
from backend.memory.hindsight import HindsightMemory, HindsightMemoryError

class Agent:
    """
    Generic Agent Core using Dependency Injection for LLM and Memory.
    """

    def __init__(self, llm: LLMService, memory: HindsightMemory):
        self._llm = llm
        self._memory = memory

    async def run(self, user_id: str, message: str) -> dict:
        """
        Run the agent loop for a user message.

        Args:
            user_id: The unique identifier for the user (used as bank_id).
            message: The user's input message.

        Returns:
            A dictionary containing the response and memory usage metadata.
        """
        # STEP 1 — Validate input
        if not user_id or not str(user_id).strip():
            raise ValueError("user_id cannot be empty.")
        if not message or not str(message).strip():
            raise ValueError("message cannot be empty.")

        user_id = str(user_id).strip()
        message = str(message).strip()

        # STEP 2 — Recall memory
        memory_used = False
        memory_context = "No relevant previous memory."
        
        try:
            await self._memory.ensure_bank(user_id)
            raw_memory = await self._memory.recall(bank_id=user_id, query=message)
            # STEP 3 — Extract useful recalled information
            # If the response string is not empty or "none" (depends on SDK)
            if raw_memory and str(raw_memory).strip() and str(raw_memory).strip().lower() != "none":
                memory_context = str(raw_memory).strip()
                memory_used = True
        except HindsightMemoryError as exc:
            # Let the memory error propagate clearly, no silent fallback
            logger.error(f"Hindsight memory recall failed: {exc}")
            raise

        # STEP 4 — Build the LLM prompt
        user_prompt = build_agent_prompt(
            memory_context=memory_context,
            user_message=message
        )

        # STEP 5 — Call the existing LLM service
        try:
            # Using the new async method that supports system and user prompts
            answer = await self._llm.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt
            )
        except LLMProviderError as exc:
            logger.error(f"LLM generation failed: {exc}")
            raise

        # STEP 6 — Remember the interaction
        interaction_summary = (
            f"User asked: {message}\n"
            f"Assistant answered: {answer}"
        )
        
        try:
            await self._memory.remember(bank_id=user_id, content=interaction_summary)
        except HindsightMemoryError as exc:
            logger.error(f"Hindsight memory store failed: {exc}")
            raise

        # STEP 7 — Return structured result
        return {
            "response": answer,
            "memory_used": memory_used,
            "memory_context": memory_context,
        }
