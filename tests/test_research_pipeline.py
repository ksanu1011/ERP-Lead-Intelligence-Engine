from __future__ import annotations

from src.domain.company_profile import CompanyProfile
from src.providers.groq_provider import GroqProvider
from src.services.research_service import ResearchService


def main() -> None:
    """Run a realistic end-to-end research analysis example for Nike."""
    company = CompanyProfile(
        name="Nike, Inc.",
        website="https://www.nike.com",
        description="Nike is a global sportswear and athletic footwear company.",
        industry="Apparel and Footwear",
        headquarters="Beaverton, Oregon, United States",
        country="United States",
        employee_count=75000,
        founded_year=1964,
        revenue="$51.2 billion",
        products=["Air Jordan", "Running shoes", "Training apparel", "Sports accessories"],
        services=["Direct-to-consumer ecommerce", "Retail operations", "Brand marketing"],
        erp_systems=["SAP S/4HANA", "Oracle ERP"],
        technologies=["Cloud infrastructure", "Data analytics", "E-commerce platforms"],
        linkedin_url="https://www.linkedin.com/company/nike",
        source_urls=[
            "https://www.nike.com",
            "https://www.linkedin.com/company/nike",
        ],
    )

    provider = GroqProvider()
    service = ResearchService(provider)
    analysis = service.analyze_company(company)
    print(analysis.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
