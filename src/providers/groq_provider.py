from __future__ import annotations

import json
import re
from typing import Any

from groq import Groq

from src.config.settings import settings
from src.interfaces.llm_provider import LLMProvider


class GroqProviderError(RuntimeError):
    """Raised when the Groq provider cannot fulfill a request."""


class GroqProvider(LLMProvider):
    """Concrete LLM provider implementation backed by Groq."""

    def __init__(self) -> None:
        """Initialize the Groq client."""
        self._client = Groq(api_key=settings.GROQ_API_KEY)
        self._model = settings.GROQ_MODEL

    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate plain text from Groq."""

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._build_messages(prompt, system_prompt),
            )
        except Exception as exc:
            raise GroqProviderError(
                f"Failed to generate text: {exc}"
            ) from exc

        content = response.choices[0].message.content

        if not isinstance(content, str) or not content.strip():
            raise GroqProviderError("Groq returned an empty response.")

        return content.strip()

    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Generate structured JSON from Groq."""

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._build_messages(prompt, system_prompt),
            )
        except Exception as exc:
            raise GroqProviderError(
                f"Failed to generate JSON: {exc}"
            ) from exc

        content = response.choices[0].message.content

        if not isinstance(content, str):
            raise GroqProviderError(
                "Groq returned a non-string response."
            )

        print("\n================ RAW LLM RESPONSE ================\n")
        print(content)
        print("\n==================================================\n")

        cleaned = self._extract_json(content)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise GroqProviderError(
                f"Unable to parse JSON.\n\nCleaned Response:\n{cleaned}\n\nError: {exc}"
            ) from exc

        if not isinstance(parsed, dict):
            raise GroqProviderError(
                "Expected a JSON object."
            )

        return parsed

    def _build_messages(
        self,
        prompt: str,
        system_prompt: str | None,
    ) -> list[dict[str, str]]:
        """Build messages for Groq."""

        messages: list[dict[str, str]] = []

        if system_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        return messages

    def _extract_json(
        self,
        content: str,
    ) -> str:
        """Extract JSON from an LLM response."""

        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]

        if content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        match = re.search(
            r"\{.*\}",
            content,
            flags=re.DOTALL,
        )

        if match:
            return match.group(0)

        return content