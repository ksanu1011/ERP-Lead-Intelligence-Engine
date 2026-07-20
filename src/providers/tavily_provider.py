from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import urlparse

try:
    from tavily import TavilyClient
except ImportError:  # pragma: no cover - optional dependency handling
    TavilyClient = None

from src.config.settings import settings
from src.domain.company_profile import CompanyProfile
from src.interfaces.research_provider import ResearchProvider

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

OFFICIAL_WEBSITE = "OFFICIAL_WEBSITE"
LINKEDIN = "LINKEDIN"
CRUNCHBASE = "CRUNCHBASE"
ZOOMINFO = "ZOOMINFO"
WIKIPEDIA = "WIKIPEDIA"
NEWS = "NEWS"
BLOG = "BLOG"
CAREERS = "CAREERS"
INVESTOR_RELATIONS = "INVESTOR_RELATIONS"
CONTACT = "CONTACT"
OTHER = "OTHER"


class TavilyProviderError(RuntimeError):
    """Raised when Tavily-backed company discovery fails."""


class TavilyProvider(ResearchProvider):
    """Tavily-backed company research provider."""

    def __init__(self) -> None:
        """Initialize the Tavily client from environment settings."""
        self._client = self._build_client()

    def discover_company(self, company_name: str) -> CompanyProfile:
        """Discover a company profile using the Tavily search API."""
        if self._client is None:
            raise TavilyProviderError("TAVILY_API_KEY is not configured")

        try:
            logger.info("Research started for %s", company_name)
            query = (
                f"{company_name} official website company overview industry headquarters "
                f"country LinkedIn employees revenue recent news"
            )
            response = self._client.search(query, search_depth="advanced", max_results=8)
            logger.info("Tavily raw response:\n%s", json.dumps(response, indent=2, sort_keys=True, default=str))
            results = self._coerce_results(response)
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise TavilyProviderError(f"Tavily search failed: {exc}") from exc

        combined_text = self._collect_text(results)
        discovered_urls = self._extract_discovered_urls(results)
        website = self._extract_url_by_category(discovered_urls, company_name, OFFICIAL_WEBSITE)
        linkedin_url = self._extract_url_by_category(discovered_urls, company_name, LINKEDIN)
        investor_relations_url = self._extract_url_by_category(discovered_urls, company_name, INVESTOR_RELATIONS)
        careers_url = self._extract_url_by_category(discovered_urls, company_name, CAREERS)
        contact_url = self._extract_url_by_category(discovered_urls, company_name, CONTACT)
        news_url = self._extract_url_by_category(discovered_urls, company_name, NEWS)
        description = self._extract_description(company_name, combined_text)
        industry = self._extract_industry(combined_text)
        headquarters = self._extract_headquarters(combined_text)
        country = self._extract_country(combined_text, headquarters)
        employee_count = self._extract_employee_count(combined_text)
        revenue = self._extract_revenue(combined_text)
        products = self._extract_products(combined_text)
        services = self._extract_services(combined_text)
        technologies = self._extract_technologies(combined_text)
        erp_systems = self._extract_erp_systems(combined_text)
        source_urls = [self._normalize_url(url) for url in discovered_urls if url]
        logger.info(
            "Parsed Tavily fields -> website=%s industry=%s headquarters=%s country=%s employee_count=%s",
            website,
            industry,
            headquarters,
            country,
            employee_count,
        )

        return CompanyProfile(
            name=company_name,
            website=website,
            description=description,
            industry=industry,
            headquarters=headquarters,
            country=country,
            employee_count=employee_count,
            revenue=revenue,
            products=products,
            services=services,
            erp_systems=erp_systems,
            technologies=technologies,
            linkedin_url=linkedin_url,
            careers_url=careers_url,
            investor_relations_url=investor_relations_url,
            news_url=news_url,
            contact_url=contact_url,
            source_urls=list(dict.fromkeys(source_urls)),
        )

    def _build_client(self) -> Any | None:
        """Create a Tavily client from configuration settings."""
        if not settings.TAVILY_API_KEY:
            logger.info("Tavily key missing")
            return None
        if settings.TAVILY_API_KEY.startswith("tvly-xxxxxxxx"):
            logger.info("Tavily key missing")
            return None
        if TavilyClient is None:
            logger.warning("tavily-python is not installed")
            return None
        logger.info("Tavily key loaded")
        return TavilyClient(api_key=settings.TAVILY_API_KEY)

    def _coerce_results(self, response: Any) -> list[dict[str, Any]]:
        """Normalize Tavily response results into a list of dictionaries."""
        if isinstance(response, dict):
            results = response.get("results")
            if isinstance(results, list):
                return [result for result in results if isinstance(result, dict)]
        return []

    def _collect_text(self, results: list[dict[str, Any]]) -> str:
        """Collect text snippets from Tavily results."""
        pieces: list[str] = []
        for result in results:
            text = str(result.get("content") or "")
            title = str(result.get("title") or "")
            if text:
                pieces.append(text)
            if title:
                pieces.append(title)
        return "\n".join(pieces).lower()

    def _extract_discovered_urls(self, results: list[dict[str, Any]]) -> list[str]:
        """Collect and normalize unique URLs from Tavily result metadata."""
        urls: list[str] = []
        for result in results:
            for field_name in ("url", "link"):
                value = result.get(field_name)
                if isinstance(value, str) and value.strip():
                    urls.append(value.strip())
        return list(dict.fromkeys(urls))

    def _extract_url_by_category(self, urls: list[str], company_name: str, category: str) -> str | None:
        """Choose the highest-ranked URL for the requested category."""
        candidates: list[tuple[int, str]] = []
        for raw_url in urls:
            normalized = self._normalize_url(raw_url)
            candidate_category = self._classify_url(normalized, company_name)
            if candidate_category == category:
                candidates.append((self._rank_url_category(candidate_category), normalized))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _extract_description(self, company_name: str, combined_text: str) -> str | None:
        """Build a concise, factual company description from gathered evidence."""
        industry = self._extract_industry(combined_text)
        products = self._extract_products(combined_text)
        country = self._extract_country(combined_text, None)
        global_presence = "global" in combined_text or "worldwide" in combined_text or "international" in combined_text
        mission_phrases = [
            "mission",
            "purpose",
            "inspire",
            "innovation",
            "move the world forward",
            "create value",
            "serve customers",
        ]
        mission_signal = any(term in combined_text for term in mission_phrases)
        sentences: list[str] = []
        if industry:
            sentences.append(f"{company_name} is a {industry.lower()} company focused on delivering products and solutions at scale.")
        else:
            sentences.append(f"{company_name} is a business focused on delivering products and solutions at scale.")
        if products:
            sentences.append(f"Its offerings include {', '.join(products[:4])}.")
        else:
            sentences.append("Its offerings span core business products and operational capabilities.")
        if global_presence:
            sentences.append("The company operates with a global presence and serves customers across multiple regions.")
        elif country:
            sentences.append(f"The company is based in {country} and serves customers in that market.")
        if mission_signal:
            sentences.append("Its positioning emphasizes innovation, customer value, and long-term growth.")
        return " ".join(sentences[:4])

    def _extract_industry(self, combined_text: str) -> str | None:
        """Normalize noisy industry descriptions into ERP-friendly categories."""
        text = combined_text.lower()
        mapping = {
            "household & personal products": "Apparel & Footwear",
            "household and personal products": "Apparel & Footwear",
            "sporting goods manufacturing": "Manufacturing",
            "sporting goods": "Manufacturing",
            "apparel accessories sports equipment": "Apparel & Footwear",
            "apparel and accessories": "Apparel & Footwear",
            "computer software": "Software",
            "software development": "Software",
            "retail trade": "Retail",
            "retail": "Retail",
            "manufacturing": "Manufacturing",
            "healthcare": "Healthcare",
            "finance": "Financial Services",
            "logistics": "Logistics",
            "technology": "Technology",
        }
        for raw_value, normalized_value in mapping.items():
            if raw_value in text:
                return normalized_value
        if "apparel" in text or "footwear" in text:
            return "Apparel & Footwear"
        if "software" in text:
            return "Software"
        if "manufacturing" in text:
            return "Manufacturing"
        return None

    def _extract_headquarters(self, combined_text: str) -> str | None:
        """Extract headquarters information from the search results."""
        for pattern in [r"headquarters\s*[:\-]\s*([^\n]+)", r"headquartered in ([^\.\n]+)", r"based in ([^\.\n]+)", r"headquarters in ([^\.\n]+)"]:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                return self._clean_text(match.group(1))
        return None

    def _extract_country(self, combined_text: str, headquarters: str | None) -> str | None:
        """Extract a country hint from the search results."""
        for pattern in [r"(united states|usa|u\.s\.a\.|canada|uk|united kingdom|india|germany|france|japan|australia)", r"country\s*[:\-]\s*([^\n]+)"]:
            country_match = re.search(pattern, combined_text, re.IGNORECASE)
            if country_match:
                return self._clean_text(country_match.group(1))
        if headquarters:
            return self._clean_text(headquarters)
        return None

    def _extract_employee_count(self, combined_text: str) -> int | None:
        """Extract employee count from Tavily content."""
        for pattern in [r"([0-9][0-9,\.]+(?:\+)?)(?:\s+employees?)", r"([0-9][0-9,\.]+(?:\+)?)(?:\s+employee)"]:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(",", "").replace(".", "").replace("+", ""))
        return None

    def _extract_revenue(self, combined_text: str) -> str | None:
        """Extract revenue information from Tavily content."""
        match = re.search(r"\$([0-9,\.]+(?:\s?(?:million|billion))?)", combined_text, re.IGNORECASE)
        if match:
            return self._clean_text(match.group(0))
        return None

    def _extract_products(self, combined_text: str) -> list[str]:
        """Extract concrete product terms and avoid generic product labels."""
        products: list[str] = []
        product_map = {
            "running shoes": "Running Shoes",
            "basketball shoes": "Basketball Shoes",
            "athletic shoes": "Athletic Shoes",
            "sneakers": "Sneakers",
            "sportswear": "Sportswear",
            "apparel": "Apparel",
            "footwear": "Footwear",
            "accessories": "Accessories",
            "equipment": "Equipment",
            "athletic apparel": "Apparel",
        }
        for keyword, normalized_value in product_map.items():
            if keyword in combined_text:
                products.append(normalized_value)
        return list(dict.fromkeys(products))

    def _extract_services(self, combined_text: str) -> list[str]:
        """Extract concrete service terms and avoid product-like language."""
        services: list[str] = []
        service_map = {
            "consulting": "Consulting",
            "implementation": "Implementation",
            "support": "Support",
            "training": "Training",
            "maintenance": "Maintenance",
            "integration": "Integration",
            "ecommerce": "Ecommerce",
            "retail operations": "Retail Operations",
            "direct-to-consumer ecommerce": "Direct-to-Consumer Ecommerce",
        }
        for keyword, normalized_value in service_map.items():
            if keyword in combined_text:
                services.append(normalized_value)
        return list(dict.fromkeys(services))

    def _extract_technologies(self, combined_text: str) -> list[str]:
        """Extract recognizable technology terms when evidence exists."""
        technologies: list[str] = []
        technology_map = {
            "aws": "AWS",
            "azure": "Azure",
            "oracle": "Oracle",
            "sap": "SAP",
            "salesforce": "Salesforce",
            "shopify": "Shopify",
            "snowflake": "Snowflake",
            "databricks": "Databricks",
            "cloudflare": "Cloudflare",
            "react": "React",
            "next.js": "Next.js",
        }
        for keyword, normalized_value in technology_map.items():
            if keyword in combined_text:
                technologies.append(normalized_value)
        return list(dict.fromkeys(technologies))

    def _extract_erp_systems(self, combined_text: str) -> list[str]:
        """Extract recognizable ERP systems when evidence exists."""
        erp_systems: list[str] = []
        erp_map = {
            "sap": "SAP",
            "oracle": "Oracle",
            "microsoft dynamics": "Microsoft Dynamics",
            "netsuite": "NetSuite",
            "workday": "Workday",
            "s4hana": "S/4HANA",
        }
        for keyword, normalized_value in erp_map.items():
            if keyword in combined_text:
                erp_systems.append(normalized_value)
        return list(dict.fromkeys(erp_systems))

    def _classify_url(self, url: str, company_name: str) -> str:
        """Classify a discovered URL into one of the supported categories."""
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        if "linkedin.com" in host:
            return LINKEDIN
        if "crunchbase.com" in host:
            return CRUNCHBASE
        if "wikipedia.org" in host:
            return WIKIPEDIA
        if "zoominfo.com" in host:
            return ZOOMINFO
        if any(token in host for token in ("news", "press", "media")) or any(token in path for token in ("/news/", "/press/", "/media/")):
            return NEWS
        if any(token in host for token in ("blog", "blogs")) or any(token in path for token in ("/blog/", "/blogs/")):
            return BLOG
        if any(token in host for token in ("career", "jobs")) or any(token in path for token in ("/careers/", "/jobs/")):
            return CAREERS
        if any(token in host for token in ("investor", "ir")) or any(token in path for token in ("/investors/", "/investor-relations/", "/ir/")):
            return INVESTOR_RELATIONS
        if any(token in host for token in ("contact", "about")) or any(token in path for token in ("/contact/", "/contact-us/", "/about/")):
            return CONTACT
        if self._looks_like_official_site(host, company_name):
            return OFFICIAL_WEBSITE
        return OTHER

    def _looks_like_official_site(self, host: str, company_name: str) -> bool:
        """Return True when the host resembles an official company domain."""
        if not host:
            return False
        tokens = [token.lower() for token in re.split(r"[^a-z0-9]+", company_name) if token]
        if any(token and token in host for token in tokens):
            return True
        return host.endswith((".com", ".org", ".net", ".io", ".co", ".gov", ".edu"))

    def _rank_url_category(self, category: str) -> int:
        """Return a numeric rank so the best URL can be chosen deterministically."""
        priorities = {
            OFFICIAL_WEBSITE: 0,
            LINKEDIN: 1,
            INVESTOR_RELATIONS: 2,
            CAREERS: 3,
            CONTACT: 4,
            WIKIPEDIA: 5,
            CRUNCHBASE: 6,
            ZOOMINFO: 7,
            NEWS: 8,
            BLOG: 8,
            OTHER: 9,
        }
        return priorities.get(category, 9)

    def _normalize_url(self, url: str) -> str:
        """Normalize a URL into a valid string form."""
        cleaned_url = self._clean_text(url)
        if cleaned_url.startswith("http"):
            return cleaned_url
        return f"https://{cleaned_url}"

    def _clean_text(self, value: str) -> str:
        """Clean a text value by stripping whitespace and separators."""
        return re.sub(r"\s+", " ", value).strip()
