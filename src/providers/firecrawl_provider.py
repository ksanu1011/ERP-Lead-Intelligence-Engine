from __future__ import annotations

from src.domain.company_profile import CompanyProfile
from src.interfaces.research_provider import ResearchProvider


class FirecrawlProviderError(RuntimeError):
    """Raised when Firecrawl-based company discovery fails."""


class FirecrawlProvider(ResearchProvider):
    """Placeholder Firecrawl-backed company research provider."""

    def discover_company(self, company_name: str) -> CompanyProfile:
        """Return a placeholder company profile for the supplied company name."""
        try:
            return CompanyProfile(
                name=company_name,
                website=f"https://www.{company_name.lower().replace(' ', '')}.com",
                description=None,
                industry=None,
                headquarters=None,
                country=None,
                employee_count=None,
                founded_year=None,
                revenue=None,
                products=[],
                services=[],
                erp_systems=[],
                technologies=[],
                linkedin_url=None,
                source_urls=[f"https://www.{company_name.lower().replace(' ', '')}.com"],
            )
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise FirecrawlProviderError(f"Failed to discover company: {exc}") from exc
