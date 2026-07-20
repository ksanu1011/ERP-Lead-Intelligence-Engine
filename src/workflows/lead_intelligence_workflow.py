from __future__ import annotations

from src.domain.company_profile import CompanyProfile
from src.domain.lead_report import LeadReport
from src.exporters.excel_exporter import ExcelExporter
from src.services.recommendation_service import RecommendationService
from src.services.research_service import ResearchService


class LeadIntelligenceWorkflowError(RuntimeError):
    """Raised when the lead intelligence workflow cannot complete."""


class LeadIntelligenceWorkflow:
    """Orchestrate company research, recommendation, and export into a lead report."""

    def __init__(
        self,
        research_service: ResearchService,
        recommendation_service: RecommendationService,
        excel_exporter: ExcelExporter,
    ) -> None:
        """Store the injected services and exporter."""
        self._research_service = research_service
        self._recommendation_service = recommendation_service
        self._excel_exporter = excel_exporter

    def run(self, company: CompanyProfile, output_path: str) -> LeadReport:
        """Run the full lead intelligence workflow for a company."""
        try:
            analysis = self._research_service.analyze_company(company)
            recommendation = self._recommendation_service.recommend(analysis)
            report = LeadReport(
                company=company,
                analysis=analysis,
                recommendation=recommendation,
            )
            self._excel_exporter.export(report, output_path)
            return report
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise LeadIntelligenceWorkflowError(f"Lead intelligence workflow failed: {exc}") from exc
