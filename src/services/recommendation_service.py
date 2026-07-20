from __future__ import annotations

from typing import Any

from src.domain.business_analysis import BusinessAnalysis
from src.domain.erp_recommendation import ERPRecommendation
from src.interfaces.llm_provider import LLMProvider


class RecommendationServiceError(RuntimeError):
    """Raised when ERP recommendations cannot be produced."""


class RecommendationService:
    """Service for transforming a business analysis into an ERP recommendation."""

    def __init__(self, llm: LLMProvider) -> None:
        """Initialize the recommendation service."""
        self._llm = llm

    def recommend(self, analysis: BusinessAnalysis) -> ERPRecommendation:
        """Generate an ERP recommendation."""
        prompt = self._build_prompt(analysis)

        try:
            payload = self._llm.generate_json(
                prompt,
                system_prompt=self._build_system_prompt(),
            )
        except Exception as exc:
            raise RecommendationServiceError(
                f"LLM generation failed: {exc}"
            ) from exc

        try:
            payload = self._normalize_payload(payload)
            return self._parse_recommendation(payload)
        except RecommendationServiceError:
            raise
        except Exception as exc:
            raise RecommendationServiceError(
                f"Recommendation validation failed: {exc}"
            ) from exc

    def _build_prompt(self, analysis: BusinessAnalysis) -> str:
        """Create the user prompt."""

        return f"""
Create an ERP recommendation based on the following business analysis.

Business Summary:
{analysis.summary}

Digital Maturity:
{analysis.digital_maturity}

Business Challenges:
{", ".join(analysis.business_challenges)}

ERP Opportunities:
{", ".join(analysis.erp_opportunities)}

Transformation Goals:
{", ".join(analysis.transformation_goals)}

Decision Makers:
{", ".join(analysis.decision_makers)}

Recommended Modules:
{", ".join(analysis.recommended_modules)}

Confidence Score:
{analysis.confidence_score}
"""

    def _build_system_prompt(self) -> str:
        """Create the system prompt."""

        return """
You are a Senior ERP Consultant at Inoday Consultancy Services.

Return ONLY valid JSON.

Do NOT return markdown.

Do NOT return code fences.

Do NOT explain anything.

The JSON MUST EXACTLY match this schema.

{
    "recommended_erp": "string",
    "recommended_modules": [
        "string"
    ],
    "implementation_priority": "string",
    "expected_business_value": [
        "string"
    ],
    "estimated_timeline": "string",
    "implementation_risks": [
        "string"
    ],
    "rationale": "string",
    "confidence_score": 0.0
}

Rules:

- expected_business_value MUST be a list.
- recommended_modules MUST be a list.
- implementation_risks MUST be a list.
- confidence_score MUST be a float.
- Return ONLY JSON.
"""

    def _normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normalize common LLM mistakes."""

        if not isinstance(payload, dict):
            raise RecommendationServiceError(
                "LLM returned a non-object JSON payload."
            )

        payload = dict(payload)

        list_fields = (
            "recommended_modules",
            "expected_business_value",
            "implementation_risks",
        )

        for field in list_fields:
            if field in payload:
                payload[field] = self._normalize_list(payload[field])

        text_fields = (
            "recommended_erp",
            "implementation_priority",
            "estimated_timeline",
            "rationale",
        )

        for field in text_fields:
            if field in payload and isinstance(payload[field], str):
                payload[field] = payload[field].strip()

        if "confidence_score" in payload:
            try:
                payload["confidence_score"] = float(payload["confidence_score"])
            except Exception:
                pass

        return payload

    def _normalize_list(self, value: Any) -> list[str]:
        """Normalize values into a list of strings."""

        if value is None:
            return []

        if isinstance(value, list):
            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

        if isinstance(value, str):
            value = value.strip()

            if "," in value:
                return [
                    item.strip()
                    for item in value.split(",")
                    if item.strip()
                ]

            return [value]

        return [str(value).strip()]

    def _parse_recommendation(
        self,
        payload: dict[str, Any],
    ) -> ERPRecommendation:
        """Validate the ERP recommendation."""

        try:
            return ERPRecommendation.model_validate(payload)
        except Exception as exc:
            raise RecommendationServiceError(
                f"Invalid recommendation payload: {exc}"
            ) from exc