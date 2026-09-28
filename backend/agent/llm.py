"""
backend/agent/llm.py
--------------------
Provider-agnostic LLM service.

Usage (from anywhere in the backend):

    from backend.agent.llm import LLMService

    llm = LLMService()
    response = await llm.generate("You are an assistant.", "Tell me a joke.")

The Agent Core will always call LLMService — it never imports Groq directly.
Adding a new provider later means adding a branch here, not touching the Agent Core.
"""

from __future__ import annotations

from backend.config import config


# ── Custom exceptions ─────────────────────────────────────────────────────────

class LLMConfigError(Exception):
    """Raised when the LLM cannot be initialised due to bad/missing configuration."""


class LLMProviderError(Exception):
    """Raised when the provider returns an unexpected or empty response."""


# ── Provider implementations ──────────────────────────────────────────────────

async def _call_groq_async(system_prompt: str, user_prompt: str, model: str, api_key: str) -> str:
    """Send a prompt to the Groq API asynchronously and return the text response."""
    from groq import AsyncGroq  # imported lazily so other providers don't need groq installed

    client = AsyncGroq(api_key=api_key)
    completion = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    )
    text = completion.choices[0].message.content
    if not text or not text.strip():
        raise LLMProviderError("Groq returned an empty response.")
    return text.strip()


def _call_groq(prompt: str, model: str, api_key: str) -> str:
    """Synchronous fallback for smoke tests."""
    from groq import Groq

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    text = completion.choices[0].message.content
    if not text or not text.strip():
        raise LLMProviderError("Groq returned an empty response.")
    return text.strip()


# Map provider name → callable
_PROVIDERS_ASYNC: dict[str, object] = {
    "groq": _call_groq_async,
}

_PROVIDERS_SYNC: dict[str, object] = {
    "groq": _call_groq,
}


# ── Public service class ──────────────────────────────────────────────────────

class LLMService:
    """
    Thin wrapper around an LLM provider.

    Configuration is read from the global config object (which reads from .env).
    The caller only ever calls `generate()` — provider details are hidden.
    """

    def __init__(self) -> None:
        self._provider_name = config.LLM_PROVIDER.lower().strip()
        self._model = config.LLM_MODEL
        self._api_key = config.LLM_API_KEY

        if not self._api_key:
            raise LLMConfigError(
                f"LLM_API_KEY is not set. "
                f"Add it to your .env file (provider: {self._provider_name})."
            )

        if self._provider_name not in _PROVIDERS_ASYNC:
            supported = ", ".join(_PROVIDERS_ASYNC.keys())
            raise LLMConfigError(
                f"Unknown LLM provider '{self._provider_name}'. "
                f"Supported providers: {supported}."
            )

        self._call_async = _PROVIDERS_ASYNC[self._provider_name]
        self._call_sync = _PROVIDERS_SYNC[self._provider_name]

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a system and user prompt to the configured LLM asynchronously.

        Args:
            system_prompt: Instructions for the model.
            user_prompt: The user's input.

        Returns:
            The model's response as a plain string.

        Raises:
            LLMProviderError: If the API call fails or returns an empty response.
        """
        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt must not be empty.")

        try:
            return await self._call_async(system_prompt, user_prompt, self._model, self._api_key)
        except LLMConfigError:
            raise
        except LLMProviderError:
            raise
        except Exception as exc:
            raise LLMProviderError(
                f"LLM request failed ({self._provider_name}/{self._model}): {exc}"
            ) from exc

    def generate_sync(self, prompt: str) -> str:
        """Legacy synchronous generate for smoke tests."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt must not be empty.")

        try:
            return self._call_sync(prompt, self._model, self._api_key)
        except LLMConfigError:
            raise
        except LLMProviderError:
            raise
        except Exception as exc:
            raise LLMProviderError(
                f"LLM request failed ({self._provider_name}/{self._model}): {exc}"
            ) from exc

    # ── Convenience repr (no secrets) ────────────────────────────────────────
    def __repr__(self) -> str:
        return f"LLMService(provider={self._provider_name!r}, model={self._model!r})"
