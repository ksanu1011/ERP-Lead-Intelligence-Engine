from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class CompanyProfile(BaseModel):
    """Factual profile information for a company."""

    name: str = Field(..., description="Official company name.")
    website: HttpUrl | None = Field(default=None, description="Company website URL.")
    description: str | None = Field(default=None, description="Short factual description of the company.")
    industry: str | None = Field(default=None, description="Primary industry or business sector.")
    headquarters: str | None = Field(default=None, description="Primary headquarters location.")
    country: str | None = Field(default=None, description="Country where the company is based.")
    employee_count: int | None = Field(default=None, description="Approximate number of employees.")
    founded_year: int | None = Field(default=None, description="Year the company was founded.")
    revenue: str | None = Field(default=None, description="Reported revenue or revenue range.")
    products: list[str] = Field(default_factory=list, description="Products or offerings sold by the company.")
    services: list[str] = Field(default_factory=list, description="Services offered by the company.")
    erp_systems: list[str] = Field(default_factory=list, description="ERP systems or platforms associated with the company.")
    technologies: list[str] = Field(default_factory=list, description="Technology stack or platforms used by the company.")
    linkedin_url: HttpUrl | None = Field(default=None, description="Company LinkedIn profile URL.")
    source_urls: list[HttpUrl] = Field(default_factory=list, description="Source URLs used to gather the profile information.")

    @field_validator("employee_count")
    @classmethod
    def validate_employee_count(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("employee_count must be non-negative")
        return value

    @field_validator("founded_year")
    @classmethod
    def validate_founded_year(cls, value: int | None) -> int | None:
        if value is not None and value < 1800:
            raise ValueError("founded_year must be at least 1800")
        return value

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
    }
