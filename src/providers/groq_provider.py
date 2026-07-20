from __future__ import annotations

import json
from typing import Any

from groq import Groq

from src.config.settings import settings
from src.interfaces.llm_provider import LLMProvider


class GroqProviderError(RuntimeError):
    """Raised when the Groq provider cannot fulfill a request."""


class GroqProvider(LLMProvider):
    """Concrete LLM provider implementation backed by Groq."""

    def __init__(self) -> None:
        """Initialize the Groq client using application settings."""
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        self._model = settings.GROQ_MODEL

    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate plain-text content from the Groq API."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._build_messages(prompt, system_prompt),
            )
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise GroqProviderError(f"Failed to generate text: {exc}") from exc

        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise GroqProviderError("Groq returned an empty text response")
        return content

    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Generate and parse JSON content from the Groq API."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._build_messages(prompt, system_prompt),
            )
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise GroqProviderError(f"Failed to generate JSON: {exc}") from exc

        content = response.choices[0].message.content
        if not isinstance(content, str):
            raise GroqProviderError("Groq returned a non-string JSON response")

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise GroqProviderError(f"Groq returned invalid JSON: {exc}") from exc

        if not isinstance(parsed, dict):
            raise GroqProviderError("Groq returned JSON that is not an object")
        return parsed

    def _build_messages(
        self,
        prompt: str,
        system_prompt: str | None,
    ) -> list[dict[str, str]]:
        """Build the chat message list for the Groq API."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages
