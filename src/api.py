from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from src.domain.business_analysis import BusinessAnalysis
from src.domain.company_profile import CompanyProfile
from src.domain.erp_recommendation import ERPRecommendation
from src.exporters.excel_exporter import ExcelExporter
from src.providers.groq_provider import GroqProvider
from src.providers.tavily_provider import TavilyProvider
from src.services.company_research_service import CompanyResearchService
from src.services.recommendation_service import RecommendationService
from src.services.research_service import ResearchService
from src.workflows.lead_intelligence_workflow import LeadIntelligenceWorkflow, LeadIntelligenceWorkflowError


class AnalyzeRequest(BaseModel):
    """Request payload for the company analysis endpoint."""

    company_name: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class AnalyzeResponse(BaseModel):
    """Response payload for the analysis endpoint."""

    status: str = Field(default="success")
    company: CompanyProfile
    analysis: BusinessAnalysis
    recommendation: ERPRecommendation
    excel_report: str


class HealthResponse(BaseModel):
    """Health check response payload."""

    service: str
    status: str


app = FastAPI(title="ERP Lead Intelligence Engine", version="1.0.0")


def get_workflow() -> LeadIntelligenceWorkflow:
    """Create the workflow with dependency-injected services."""
    provider = GroqProvider()
    research_service = ResearchService(provider)
    recommendation_service = RecommendationService(provider)
    excel_exporter = ExcelExporter()
    return LeadIntelligenceWorkflow(
        research_service=research_service,
        recommendation_service=recommendation_service,
        excel_exporter=excel_exporter,
    )


def get_company_research_service() -> CompanyResearchService:
    """Create the company research service with the injected provider."""
    research_provider = TavilyProvider()
    return CompanyResearchService(research_provider)


@app.get("/", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return the service health status."""
    return HealthResponse(service="ERP Lead Intelligence Engine", status="running")


@app.post("/analyze", response_model=AnalyzeResponse, status_code=200)
def analyze_company(
    request: AnalyzeRequest,
    workflow: LeadIntelligenceWorkflow = Depends(get_workflow),
    company_research_service: CompanyResearchService = Depends(get_company_research_service),
) -> AnalyzeResponse:
    """Analyze a company and produce a lead report Excel export."""
    try:
        company = company_research_service.discover(request.company_name)
        output_path = _build_output_path(request.company_name)
        report = workflow.run(company, output_path)
        return AnalyzeResponse(
            status="success",
            company=report.company,
            analysis=report.analysis,
            recommendation=report.recommendation,
            excel_report=output_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LeadIntelligenceWorkflowError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive boundary
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.exception_handler(404)
def not_found_handler(_: Request, exc: Exception) -> Any:
    """Return a consistent 404 response."""
    return {"detail": "Not found"}


def _build_output_path(company_name: str) -> str:
    """Build a deterministic output path for an analysis export."""
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", company_name).strip("_").lower() or "company"
    return str(output_dir / f"{slug}_report.xlsx")
