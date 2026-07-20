from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.company_profile import CompanyProfile


class ResearchProvider(ABC):
    """Abstract interface for company research providers."""

    @abstractmethod
    def discover_company(self, company_name: str) -> CompanyProfile:
        """Discover and return a company profile for the provided company name."""
        raise NotImplementedError
