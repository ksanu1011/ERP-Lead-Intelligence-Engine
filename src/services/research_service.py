from __future__ import annotations

from typing import Any

from src.domain.business_analysis import BusinessAnalysis
from src.domain.company_profile import CompanyProfile
from src.interfaces.llm_provider import LLMProvider


class ResearchServiceError(RuntimeError):
    """Raised when company research analysis cannot be completed."""


class ResearchService:
    """Service for transforming a company profile into a business analysis."""

    def __init__(self, llm: LLMProvider) -> None:
        """Store the injected LLM provider."""
        self._llm = llm

    def analyze_company(self, company: CompanyProfile) -> BusinessAnalysis:
        """Generate a business analysis for the provided company profile."""
        prompt = self._build_prompt(company)
        try:
            payload = self._llm.generate_json(prompt, system_prompt=self._build_system_prompt())
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise ResearchServiceError(f"LLM generation failed: {exc}") from exc

        try:
            return self._parse_analysis(payload)
        except Exception as exc:
            raise ResearchServiceError(f"Business analysis validation failed: {exc}") from exc

    def _build_prompt(self, company: CompanyProfile) -> str:
        """Build a detailed prompt from the company profile."""
        return (
            "Analyze the following company profile and produce a structured business analysis. "
            "Return valid JSON matching the BusinessAnalysis schema.\n\n"
            f"Company name: {company.name}\n"
            f"Website: {company.website}\n"
            f"Description: {company.description or 'N/A'}\n"
            f"Industry: {company.industry or 'N/A'}\n"
            f"Headquarters: {company.headquarters or 'N/A'}\n"
            f"Country: {company.country or 'N/A'}\n"
            f"Employee count: {company.employee_count if company.employee_count is not None else 'N/A'}\n"
            f"Founded year: {company.founded_year if company.founded_year is not None else 'N/A'}\n"
            f"Revenue: {company.revenue or 'N/A'}\n"
            f"Products: {', '.join(company.products) if company.products else 'N/A'}\n"
            f"Services: {', '.join(company.services) if company.services else 'N/A'}\n"
            f"ERP systems: {', '.join(company.erp_systems) if company.erp_systems else 'N/A'}\n"
            f"Technologies: {', '.join(company.technologies) if company.technologies else 'N/A'}\n"
            f"LinkedIn: {company.linkedin_url}\n"
            f"Source URLs: {', '.join(str(url) for url in company.source_urls) if company.source_urls else 'N/A'}"
        )

    def _build_system_prompt(self) -> str:
        """Build a system prompt that constrains the model output."""
        return (
            "You are an ERP business analysis assistant. "
            "Return only valid JSON with the following keys: summary, digital_maturity, "
            "business_challenges, erp_opportunities, transformation_goals, decision_makers, "
            "recommended_modules, confidence_score."
        )

    def _parse_analysis(self, payload: dict[str, Any]) -> BusinessAnalysis:
        """Validate and parse the LLM JSON payload into a BusinessAnalysis."""
        try:
            return BusinessAnalysis.model_validate(payload)
        except Exception as exc:
            raise ResearchServiceError(f"Invalid analysis payload: {exc}") from exc
