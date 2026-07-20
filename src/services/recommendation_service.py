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
        """Store the injected LLM provider."""
        self._llm = llm

    def recommend(self, analysis: BusinessAnalysis) -> ERPRecommendation:
        """Generate an ERP recommendation for the provided business analysis."""
        prompt = self._build_prompt(analysis)
        try:
            payload = self._llm.generate_json(prompt, system_prompt=self._build_system_prompt())
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise RecommendationServiceError(f"LLM generation failed: {exc}") from exc

        try:
            return self._parse_recommendation(payload)
        except Exception as exc:
            raise RecommendationServiceError(f"Recommendation validation failed: {exc}") from exc

    def _build_prompt(self, analysis: BusinessAnalysis) -> str:
        """Build a detailed prompt from the business analysis."""
        return (
            "Create an ERP recommendation for the following business analysis. "
            "Return valid JSON matching the ERPRecommendation schema.\n\n"
            f"Summary: {analysis.summary}\n"
            f"Digital maturity: {analysis.digital_maturity}\n"
            f"Business challenges: {', '.join(analysis.business_challenges) if analysis.business_challenges else 'N/A'}\n"
            f"ERP opportunities: {', '.join(analysis.erp_opportunities) if analysis.erp_opportunities else 'N/A'}\n"
            f"Transformation goals: {', '.join(analysis.transformation_goals) if analysis.transformation_goals else 'N/A'}\n"
            f"Decision makers: {', '.join(analysis.decision_makers) if analysis.decision_makers else 'N/A'}\n"
            f"Recommended modules: {', '.join(analysis.recommended_modules) if analysis.recommended_modules else 'N/A'}\n"
            f"Confidence score: {analysis.confidence_score}"
        )

    def _build_system_prompt(self) -> str:
        """Build a system prompt that constrains the model output."""
        return (
            "You are a senior ERP consulting expert working for Inoday Consultancy Services. "
            "Provide a practical recommendation focused on the recommended ERP platform, "
            "recommended ERP modules, business justification, expected business benefits, "
            "implementation risks, estimated implementation priority, and suggested next sales actions. "
            "Return only valid JSON with the following keys: recommended_erp, recommended_modules, "
            "implementation_priority, expected_business_value, estimated_timeline, "
            "implementation_risks, rationale, confidence_score."
        )

    def _parse_recommendation(self, payload: dict[str, Any]) -> ERPRecommendation:
        """Validate and parse the LLM JSON payload into an ERPRecommendation."""
        try:
            return ERPRecommendation.model_validate(payload)
        except Exception as exc:
            raise RecommendationServiceError(f"Invalid recommendation payload: {exc}") from exc
