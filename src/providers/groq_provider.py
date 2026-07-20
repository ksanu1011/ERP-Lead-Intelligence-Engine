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
        api_key = settings.GROQ_API_KEY
        self._client = Groq(api_key=api_key) if api_key else None
        self._model = settings.GROQ_MODEL

    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate plain text from Groq."""

        if self._client is None:
            return self._build_fallback_text(prompt, system_prompt)

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._build_messages(prompt, system_prompt),
            )
        except Exception:
            return self._build_fallback_text(prompt, system_prompt)

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

        if self._client is None:
            return self._build_fallback_payload(prompt, system_prompt)

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._build_messages(prompt, system_prompt),
            )
        except Exception:
            return self._build_fallback_payload(prompt, system_prompt)

        content = response.choices[0].message.content

        if not isinstance(content, str):
            return self._build_fallback_payload(prompt, system_prompt)

        print("\n================ RAW LLM RESPONSE ================\n")
        print(content)
        print("\n==================================================\n")

        cleaned = self._extract_json(content)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return self._build_fallback_payload(prompt, system_prompt)

        if not isinstance(parsed, dict):
            return self._build_fallback_payload(prompt, system_prompt)

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

    def _build_fallback_payload(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """Return a deterministic fallback payload when Groq is unavailable."""
        prompt_text = " ".join([prompt or "", system_prompt or ""]).lower()

        if "recommended_erp" in prompt_text or "implementation_priority" in prompt_text:
            return {
                "recommended_erp": "Microsoft Dynamics 365 Business Central",
                "recommended_modules": ["Finance", "Sales", "Inventory"],
                "implementation_priority": "Phase 1",
                "expected_business_value": ["Faster reporting", "Improved operational visibility"],
                "estimated_timeline": "4-6 months",
                "implementation_risks": ["Data migration complexity", "Change management adoption"],
                "rationale": "A pragmatic ERP recommendation using the available company profile when live LLM generation is unavailable.",
                "confidence_score": 0.4,
            }

        return {
            "summary": "The company profile indicates a strong need for ERP modernization and better cross-functional visibility.",
            "digital_maturity": "Moderate",
            "business_challenges": ["Fragmented operations", "Limited reporting visibility"],
            "erp_opportunities": ["Standardize finance and supply-chain processes", "Improve data visibility"],
            "transformation_goals": ["Improve operational efficiency", "Strengthen reporting capabilities"],
            "decision_makers": ["CFO", "COO", "IT Director"],
            "recommended_modules": ["Finance", "Inventory", "Supply Chain"],
            "confidence_score": 0.4,
        }

    def _build_fallback_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Return a fallback text response when Groq is unavailable."""
        return (
            "Groq generation is currently unavailable, so a fallback response was used. "
            f"Prompt: {prompt[:120]}"
        )

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