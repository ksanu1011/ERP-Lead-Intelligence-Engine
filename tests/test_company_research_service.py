from src.domain.company_profile import CompanyProfile
from src.utils.company_profile_merge import merge_company_profiles


def test_merge_company_profiles_prefers_primary_values_and_dedupes_lists() -> None:
    primary = CompanyProfile(
        name="Contoso",
        website="https://contoso.com",
        industry="Software",
        headquarters="Seattle",
        country="United States",
        products=["Product A", "Product B"],
        services=["Consulting"],
        source_urls=["https://contoso.com"],
    )
    secondary = CompanyProfile(
        name="Contoso",
        website="https://example.com",
        industry=None,
        headquarters=None,
        country=None,
        products=["Product B", "Product C"],
        services=["Consulting", "Support"],
        source_urls=["https://example.com"],
    )

    merged = merge_company_profiles(primary, secondary)

    assert merged.name == "Contoso"
    assert str(merged.website) == "https://contoso.com/"
    assert merged.industry == "Software"
    assert merged.headquarters == "Seattle"
    assert merged.country == "United States"
    assert merged.products == ["Product A", "Product B", "Product C"]
    assert merged.services == ["Consulting", "Support"]
    assert [str(url) for url in merged.source_urls] == ["https://contoso.com/", "https://example.com/"]


def test_merge_company_profiles_ignores_unknown_placeholders() -> None:
    primary = CompanyProfile(
        name="Contoso",
        website=None,
        industry="Unknown",
        headquarters="Unknown",
        country="Unknown",
        employee_count=None,
    )
    secondary = CompanyProfile(
        name="Contoso",
        website="https://example.com",
        industry="Retail",
        headquarters="Beaverton",
        country="United States",
        employee_count=10000,
    )

    merged = merge_company_profiles(primary, secondary)

    assert str(merged.website) == "https://example.com/"
    assert merged.industry == "Retail"
    assert merged.headquarters == "Beaverton"
    assert merged.country == "United States"
    assert merged.employee_count == 10000


def test_merge_company_profiles_prefers_official_website_over_linkedin() -> None:
    primary = CompanyProfile(
        name="Nike",
        website="https://www.linkedin.com/company/nike",
        linkedin_url="https://www.linkedin.com/company/nike",
        source_urls=["https://www.linkedin.com/company/nike"],
    )
    secondary = CompanyProfile(
        name="Nike",
        website="https://www.nike.com",
        linkedin_url=None,
        source_urls=["https://www.nike.com"],
    )

    merged = merge_company_profiles(primary, secondary)

    assert str(merged.website).startswith("https://www.nike.com")
    assert str(merged.linkedin_url).startswith("https://www.linkedin.com/company/nike")
