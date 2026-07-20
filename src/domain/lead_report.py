from __future__ import annotations

from datetime import datetime, UTC

from pydantic import BaseModel, ConfigDict, Field

from src.domain.business_analysis import BusinessAnalysis
from src.domain.company_profile import CompanyProfile
from src.domain.erp_recommendation import ERPRecommendation


class LeadReport(BaseModel):
    """Complete ERP lead intelligence report combining profile, analysis, and recommendation."""

    company: CompanyProfile
    analysis: BusinessAnalysis
    recommendation: ERPRecommendation
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    report_version: str = Field(default="1.0.0")

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    def executive_summary(self) -> str:
        """Return a concise human-readable executive summary."""
        main_challenge = (
            self.analysis.business_challenges[0]
            if self.analysis.business_challenges
            else "No major challenge identified"
        )
        return (
            f"{self.company.name} operates in {self.company.industry or 'unknown industry'} and is "
            f"assessed as {self.analysis.digital_maturity}. The main challenge is '{main_challenge}'. "
            f"Recommended ERP: {self.recommendation.recommended_erp}. "
            f"Confidence score: {self.analysis.confidence_score:.2f}."
        )

    def to_dict(self) -> dict[str, object]:
        """Return the report as a dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Return the report as a JSON string."""
        return self.model_dump_json(indent=2)
