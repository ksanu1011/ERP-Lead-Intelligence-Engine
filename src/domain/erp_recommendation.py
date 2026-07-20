from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ERPRecommendation(BaseModel):
    """ERP solution recommendation derived from business analysis."""

    recommended_erp: str = Field(..., description="Recommended ERP platform or solution.")
    recommended_modules: list[str] = Field(default_factory=list, description="ERP modules recommended for implementation.")
    implementation_priority: str = Field(..., description="Priority level for rollout or implementation.")
    expected_business_value: list[str] = Field(default_factory=list, description="Anticipated business value from the recommendation.")
    estimated_timeline: str = Field(..., description="Estimated implementation timeline.")
    implementation_risks: list[str] = Field(default_factory=list, description="Key implementation risks or cautions.")
    rationale: str = Field(..., description="Reasoning behind the ERP recommendation.")
    confidence_score: float = Field(..., description="Confidence score for the recommendation, ranging from 0.0 to 1.0.")

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
