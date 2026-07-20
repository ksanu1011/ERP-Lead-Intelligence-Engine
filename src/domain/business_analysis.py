from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class BusinessAnalysis(BaseModel):
    """AI-generated business reasoning for a company based on factual profile data."""

    summary: str = Field(..., description="High-level summary of the company's business context and outlook.")
    digital_maturity: str = Field(..., description="Assessment of the company's digital maturity level.")
    business_challenges: list[str] = Field(default_factory=list, description="Key business challenges identified for the company.")
    erp_opportunities: list[str] = Field(default_factory=list, description="Potential ERP-related opportunities or gaps.")
    transformation_goals: list[str] = Field(default_factory=list, description="Strategic transformation goals relevant to the business.")
    decision_makers: list[str] = Field(default_factory=list, description="Likely decision makers or stakeholder roles involved.")
    recommended_modules: list[str] = Field(default_factory=list, description="Recommended ERP modules or solution areas.")
    confidence_score: float = Field(..., description="Confidence score for the analysis, ranging from 0.0 to 1.0.")

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_score(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return value

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }
