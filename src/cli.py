from __future__ import annotations

import argparse
import sys
from typing import Sequence

from src.domain.company_profile import CompanyProfile
from src.exporters.excel_exporter import ExcelExporter
from src.providers.groq_provider import GroqProvider
from src.services.recommendation_service import RecommendationService
from src.services.research_service import ResearchService
from src.workflows.lead_intelligence_workflow import LeadIntelligenceWorkflow


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="erp-ai")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a company and export a lead report")
    analyze_parser.add_argument("--company-name", required=True)
    analyze_parser.add_argument("--website", required=True)
    analyze_parser.add_argument("--industry")
    analyze_parser.add_argument("--headquarters")
    analyze_parser.add_argument("--country")
    analyze_parser.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        try:
            company = CompanyProfile(
                name=args.company_name,
                website=args.website,
                description=None,
                industry=args.industry,
                headquarters=args.headquarters,
                country=args.country,
                employee_count=None,
                founded_year=None,
                revenue=None,
                products=[],
                services=[],
                erp_systems=[],
                technologies=[],
                linkedin_url=None,
                source_urls=[args.website],
            )
            provider = GroqProvider()
            research_service = ResearchService(provider)
            recommendation_service = RecommendationService(provider)
            excel_exporter = ExcelExporter()
            workflow = LeadIntelligenceWorkflow(
                research_service=research_service,
                recommendation_service=recommendation_service,
                excel_exporter=excel_exporter,
            )
            workflow.run(company, args.output)
            print("✓ Research completed")
            print("✓ Recommendation completed")
            print("✓ Excel report generated")
            print(args.output)
            return 0
        except Exception as exc:  # pragma: no cover - defensive boundary
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
