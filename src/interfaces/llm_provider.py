from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract interface for Large Language Model providers."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a plain-text response from the language model.

        Args:
            prompt: The user's prompt.
            system_prompt: Optional system instruction.

        Returns:
            Generated text response.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a structured JSON response from the language model.

        Args:
            prompt: The user's prompt.
            system_prompt: Optional system instruction.

        Returns:
            Parsed JSON response.
        """
        raise NotImplementedError