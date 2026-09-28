"""
backend/memory/hindsight.py
---------------------------
Hindsight Memory Service wrapper.

Provides a clean async interface for Agent Core to store, recall, and reflect on memories 
using Hindsight.
"""

import logging
from backend.config import config
from hindsight_client import Hindsight

logger = logging.getLogger(__name__)

class HindsightConfigError(Exception):
    """Raised when Hindsight cannot be initialized due to bad/missing configuration."""

class HindsightMemoryError(Exception):
    """Raised when an operation with Hindsight fails (e.g., connection issues)."""

class HindsightMemory:
    """
    Thin async wrapper around the Hindsight client.
    
    Configuration is read from the global config object (which reads from .env).
    Must be used in an async context.
    """

    def __init__(self) -> None:
        self._url = config.HINDSIGHT_URL
        self._api_key = config.HINDSIGHT_API_KEY

        if not self._url:
            raise HindsightConfigError("HINDSIGHT_URL is not configured.")

        try:
            self._client = Hindsight(
                base_url=self._url,
                api_key=self._api_key or None
            )
        except Exception as exc:
            raise HindsightConfigError(f"Failed to initialize Hindsight client: {exc}") from exc

    async def remember(self, bank_id: str, content: str, context: str | None = None) -> None:
        """
        Store information in the memory bank asynchronously.

        Args:
            bank_id: A logical namespace identifier (e.g. user_id, conversation_id).
            content: The text content to store.
            context: Optional context for the memory.
            
        Raises:
            HindsightMemoryError: If the memory storage fails.
        """
        if not bank_id or not str(bank_id).strip():
            raise ValueError("bank_id must not be empty.")
        if not content or not str(content).strip():
            raise ValueError("content must not be empty.")

        try:
            # We pass context only if it's provided, or check if aretain accepts it.
            # According to typical Hindsight API, aretain can accept context if supported.
            # If not supported, we just pass content. 
            # Looking at standard kwargs, we can just pass them.
            if context:
                await self._client.aretain(bank_id=bank_id, content=content, context=context)
            else:
                await self._client.aretain(bank_id=bank_id, content=content)
        except Exception as exc:
            raise HindsightMemoryError(f"Failed to store memory: {exc}") from exc

    async def recall(self, bank_id: str, query: str, max_tokens: int = 4096) -> str:
        """
        Retrieve relevant memories based on a query asynchronously.

        Args:
            bank_id: A logical namespace identifier.
            query: The question or context to search for.
            max_tokens: The maximum tokens to retrieve.

        Returns:
            The retrieved memories formatted as a string.

        Raises:
            HindsightMemoryError: If the memory recall fails.
        """
        if not bank_id or not str(bank_id).strip():
            raise ValueError("bank_id must not be empty.")
        if not query or not str(query).strip():
            raise ValueError("query must not be empty.")

        try:
            response = await self._client.arecall(bank_id=bank_id, query=query)
            # The recall method usually returns an object that can be cast to string 
            # or has a specific attribute. We convert the raw response to string.
            return str(response)
        except Exception as exc:
            raise HindsightMemoryError(f"Failed to recall memory: {exc}") from exc

    async def reflect(self, bank_id: str, query: str, budget: str = "low") -> str:
        """
        Synthesize a reasoned response based on retrieved memories asynchronously.

        Args:
            bank_id: A logical namespace identifier.
            query: The question to reflect upon.
            budget: Computation budget (e.g., 'low', 'high').

        Returns:
            The synthesized answer.

        Raises:
            HindsightMemoryError: If the reflection operation fails.
        """
        if not bank_id or not str(bank_id).strip():
            raise ValueError("bank_id must not be empty.")
        if not query or not str(query).strip():
            raise ValueError("query must not be empty.")

        try:
            response = await self._client.areflect(bank_id=bank_id, query=query, budget=budget)
            # Assuming the response has an answer attribute or can be cast to string
            if hasattr(response, 'answer'):
                return str(response.answer)
            return str(response)
        except Exception as exc:
            raise HindsightMemoryError(f"Failed to reflect on memory: {exc}") from exc

    async def ensure_bank(self, bank_id: str) -> None:
        """
        Ensure that the memory bank exists, creating it if it does not.

        Args:
            bank_id: A logical namespace identifier.
            
        Raises:
            HindsightMemoryError: If the server is unreachable or another error occurs.
        """
        if not bank_id or not str(bank_id).strip():
            raise ValueError("bank_id must not be empty.")
            
        try:
            # Try to get the bank config to see if it exists
            await self._client.aget_bank_config(bank_id)
            logger.debug(f"Bank '{bank_id}' already exists.")
        except Exception as exc:
            # Check if it's a 404 Not Found error
            status = getattr(exc, 'status', None)
            if status == 404 or "(404)" in str(exc):
                logger.info(f"Bank '{bank_id}' not found. Creating it...")
                try:
                    await self._client.acreate_bank(bank_id=bank_id, name=bank_id)
                    logger.debug(f"Bank '{bank_id}' created successfully.")
                except Exception as create_exc:
                    raise HindsightMemoryError(f"Failed to create bank: {create_exc}") from create_exc
            else:
                raise HindsightMemoryError(f"Error checking bank status: {exc}") from exc

    async def get_memories(self, bank_id: str, limit: int = 100) -> list:
        """
        Retrieve all memory units for a given bank.
        """
        if not bank_id or not str(bank_id).strip():
            raise ValueError("bank_id must not be empty.")
            
        try:
            response = await self._client.alist_memories(bank_id=bank_id, limit=limit)
            # The response usually has a .memories or .items or something similar.
            # Assuming it's a model with 'memories' or similar list.
            if hasattr(response, "memories"):
                return response.memories
            if hasattr(response, "items"):
                return response.items
            if hasattr(response, "memory_units"):
                return response.memory_units
                
            return []
        except Exception as exc:
            status = getattr(exc, 'status', None)
            if status == 404 or "(404)" in str(exc):
                return []  # Bank not found, so no memories
            raise HindsightMemoryError(f"Failed to list memories: {exc}") from exc

    async def close(self) -> None:
        """
        Close the underlying Hindsight client to free resources.
        """
        try:
            if hasattr(self._client, 'aclose'):
                await self._client.aclose()
            elif hasattr(self._client, 'close'):
                self._client.close()
        except Exception as exc:
            logger.warning(f"Error closing Hindsight client: {exc}")

    def __repr__(self) -> str:
        return f"HindsightMemory(url={self._url!r})"
