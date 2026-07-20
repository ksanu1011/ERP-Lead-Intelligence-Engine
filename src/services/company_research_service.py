from __future__ import annotations

import logging

from src.domain.company_profile import CompanyProfile
from src.interfaces.research_provider import ResearchProvider
from src.providers.firecrawl_provider import FirecrawlProvider
from src.providers.tavily_provider import TavilyProvider
from src.utils.company_profile_merge import merge_company_profiles

logger = logging.getLogger(__name__)


class CompanyResearchServiceError(RuntimeError):
    """Raised when company discovery cannot be completed."""


class CompanyResearchService:
    """Service for turning a company name into a fully populated company profile."""

    def __init__(self, research_provider: ResearchProvider) -> None:
        """Store the injected research provider."""
        self._research_provider = research_provider

    def discover(self, company_name: str) -> CompanyProfile:
        """Discover a company profile from the supplied company name."""
        logger.info("Research started for %s", company_name)
        logger.info("Calling TavilyProvider")
        try:
            tavily_profile = self._research_provider.discover_company(company_name)
            logger.info("Tavily completed for %s", company_name)
        except Exception as exc:  # pragma: no cover - defensive boundary
            logger.warning("Tavily failed for %s: %s", company_name, exc)
            tavily_profile = CompanyProfile(name=company_name, source_urls=[])

        firecrawl_profile = CompanyProfile(name=company_name, source_urls=[])
        if not self._has_meaningful_profile_data(tavily_profile):
            logger.info("Firecrawl fallback executing because Tavily returned no usable data")
            try:
                firecrawl_provider = FirecrawlProvider()
                firecrawl_profile = firecrawl_provider.discover_company(company_name)
                logger.info("Firecrawl completed for %s", company_name)
            except Exception as exc:  # pragma: no cover - defensive boundary
                logger.warning("Firecrawl failed for %s: %s", company_name, exc)
        else:
            logger.info("Skipping Firecrawl fallback because Tavily returned usable data")

        merged_profile = merge_company_profiles(tavily_profile, firecrawl_profile)
        logger.info("Merge completed for %s", company_name)
        return self._enrich_profile(merged_profile, company_name)

    def _enrich_profile(self, profile: CompanyProfile, company_name: str) -> CompanyProfile:
        """Populate missing profile fields with sensible defaults."""
        data: dict[str, object] = profile.model_dump()
        data["name"] = profile.name or company_name
        data["website"] = profile.website or f"https://www.{company_name.lower().replace(' ', '')}.com"
        data["industry"] = profile.industry if self._has_meaningful_value(profile.industry) else "Unknown"
        data["headquarters"] = profile.headquarters if self._has_meaningful_value(profile.headquarters) else "Unknown"
        data["country"] = profile.country if self._has_meaningful_value(profile.country) else "Unknown"
        data["employee_count"] = profile.employee_count
        data["products"] = list(profile.products or [])
        data["services"] = list(profile.services or [])
        data["linkedin_url"] = profile.linkedin_url
        data["source_urls"] = list(profile.source_urls or [])
        return CompanyProfile.model_validate(data)

    def _has_meaningful_profile_data(self, profile: CompanyProfile) -> bool:
        """Return True when the profile contains useful data beyond the company name."""
        return any(
            self._has_meaningful_value(getattr(profile, field_name, None))
            for field_name in ["website", "description", "industry", "headquarters", "country", "revenue", "linkedin_url", "employee_count"]
        ) or bool(profile.products or profile.services or profile.erp_systems or profile.technologies or profile.source_urls)

    def _has_meaningful_value(self, value: object) -> bool:
        """Return True when a value is not None, empty, or a placeholder like 'Unknown'."""
        if value is None:
            return False
        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized not in {"", "unknown", "n/a", "none"}
        return True
