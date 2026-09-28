"""
backend/agent/llm.py
--------------------
Provider-agnostic LLM service.

Usage (from anywhere in the backend):

    from backend.agent.llm import LLMService

    llm = LLMService()
    response = llm.generate("Tell me a joke.")

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

def _call_groq(prompt: str, model: str, api_key: str) -> str:
    """Send a prompt to the Groq API and return the text response."""
    from groq import Groq  # imported lazily so other providers don't need groq installed

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    text = completion.choices[0].message.content
    if not text or not text.strip():
        raise LLMProviderError("Groq returned an empty response.")
    return text.strip()


# Map provider name → callable(prompt, model, api_key) → str
_PROVIDERS: dict[str, object] = {
    "groq": _call_groq,
}


# ── Public service class ──────────────────────────────────────────────────────

class LLMService:
    """
    Thin wrapper around an LLM provider.

    Configuration is read from the global config object (which reads from .env).
    The caller only ever calls `generate(prompt)` — provider details are hidden.
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

        if self._provider_name not in _PROVIDERS:
            supported = ", ".join(_PROVIDERS.keys())
            raise LLMConfigError(
                f"Unknown LLM provider '{self._provider_name}'. "
                f"Supported providers: {supported}."
            )

        self._call = _PROVIDERS[self._provider_name]

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to the configured LLM and return the response text.

        Args:
            prompt: The user prompt string.

        Returns:
            The model's response as a plain string.

        Raises:
            LLMProviderError: If the API call fails or returns an empty response.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt must not be empty.")

        try:
            return self._call(prompt, self._model, self._api_key)
        except LLMConfigError:
            raise
        except LLMProviderError:
            raise
        except Exception as exc:
            # Re-raise as LLMProviderError so callers only need to catch one type.
            # Never include the api_key in the message.
            raise LLMProviderError(
                f"LLM request failed ({self._provider_name}/{self._model}): {exc}"
            ) from exc

    # ── Convenience repr (no secrets) ────────────────────────────────────────
    def __repr__(self) -> str:
        return f"LLMService(provider={self._provider_name!r}, model={self._model!r})"
