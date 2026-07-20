# ERP Lead Intelligence Engine

ERP Lead Intelligence Engine is an AI-powered platform for researching companies, enriching lead profiles, generating business analysis, and producing ERP recommendations. It combines company discovery, workflow orchestration, and Excel export into a single modular Python service.

## What the project does

The application can:

- discover company information from external research providers
- build a structured company profile with website, LinkedIn, industry, products, services, and technologies
- generate a business analysis for ERP opportunities
- produce an ERP recommendation
- export a lead report to Excel
- expose the workflow through a FastAPI endpoint

## Architecture overview

The codebase follows a clean, layered structure:

- src/api.py: FastAPI entrypoints for health checks and company analysis
- src/domain/: Pydantic domain models such as CompanyProfile, BusinessAnalysis, ERPRecommendation, and LeadReport
- src/providers/: integrations with external providers, including Groq and Tavily
- src/services/: application services for research, company discovery, and recommendations
- src/workflows/: orchestration layer for the end-to-end lead intelligence workflow
- src/exporters/: Excel export logic for generating report files
- src/utils/: reusable helpers such as profile merging and normalization utilities

## Main flow

1. A company name is received by the API.
2. The company research service discovers company metadata using Tavily.
3. The discovered data is normalized and merged into a CompanyProfile.
4. The workflow runs research and recommendation services to build a lead analysis.
5. The result is exported as an Excel report under the output directory.

## Key technologies

- Python 3.11+
- FastAPI for the API layer
- Pydantic v2 for validation and models
- Groq for LLM-based analysis and recommendations
- Tavily for company research enrichment
- OpenPyXL for Excel report generation

## Project structure

```text
src/
  api.py
  domain/
  interfaces/
  providers/
  services/
  utils/
  workflows/
  exporters/
tests/
output/
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -e .
```

3. Set the required environment variables in a .env file:

```env
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
```

## Run the API

```bash
uvicorn src.api:app --reload
```

Then visit:

- http://127.0.0.1:8000/docs for Swagger UI

## Run tests

```bash
pytest -q
```

## Current status

The research layer is operational and the system can discover company data, generate analyses, and export reports. The codebase remains modular so new providers or export formats can be added without rewriting the workflow.
