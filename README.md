# Copilot StartUp Backend

Comprehensive backend for startup analysis and consultation built with FastAPI and LangChain (Google Generative AI). This service provides endpoints for metrics generation, devil's-advocate analysis, competitor comparison, record queries and an LLM-backed chat agent that uses BigQuery for context.

---

## Table of contents
- Project overview
- Repo structure (detailed)
- Key files and responsibilities
- Environment variables
- Local setup & testing
- API endpoints & examples
- Notes: structured chat history
- Submodule information
- Troubleshooting

---

## Project overview

This repository hosts a FastAPI service designed to:
- Extract and summarize startup data stored in BigQuery
- Provide LangChain-driven AI endpoints for analysis and critique
- Offer a chat agent that uses BigQuery context and frontend-provided chat history

The chat agent intentionally avoids accepting raw SQL from clients: named query types and server-side SQL templates are used to ensure safety. The agent can accept structured history from the frontend for improved role-awareness.

---

## Repository structure

Root layout (key files and folders):

```
copilot-startUp-backend/
├── Dockerfile
├── hackmind-471716-005138e883ce.json   # optional local service account
├── main.py                              # FastAPI app + endpoints
├── README.md                            # (this file)
├── requirements.txt                     # Python dependencies
├── models/                              # Pydantic models
│   ├── chat.py                          # Chat request/response models (structured history)
│   └── summarize.py                     # Models for summarization/metrics
├── services/                            # Business logic & LangChain integrations
│   ├── chat_agent.py                    # Chat agent: BigQuery fetch + LangChain agent
│   ├── metrics_generator.py             # Metrics generation using LLMs
│   ├── devils_advocate.py               # Devil's advocate agent
│   ├── comparison_analysis.py           # Competitor / market analysis agent
│   └── ... (other utility services)
├── specs/                               # Git submodule for API specs (see .gitmodules)
│   └── ...                              # OpenAPI / YAML specs and helpers
└── .gitmodules                          # submodule reference to `specs`
```

Notes:
- `models/chat.py` defines `ChatMessage` (structured roles) and `ChatRequest.history`.
- `services/chat_agent.py` fetches context from BigQuery (hard-coded server-side SQL) and includes structured history in the agent prompt.

---

## Key files & responsibilities

- `main.py`:
  - FastAPI application and endpoints.
  - Handles lazy BigQuery client initialization to avoid import-time credential failures.
  - `/chat` endpoint forwards structured `history` to the chat agent.

- `models/chat.py`:
  - `ChatMessage` Pydantic model: `role: Literal['user','assistant']`, `text: str`.
  - `ChatRequest`: `message`, `query_type`, `startup_id`, `history: Optional[List[ChatMessage]]`.

- `services/chat_agent.py`:
  - `fetch_bigquery()` helper wraps BigQuery client and supports parameterized queries.
  - `run_chat_agent()` orchestrates fetching both tables (`BQ_TABLE_ID` and `BQ_TABLE_STARTUP_PITCH_ID`), builds a prompt that includes truncated JSON previews, and calls a LangChain agent.
  - The agent uses tools: `bigquery_query` (executes server-side SQL) and `summarize`.
  - Web-search (SerpAPI) integration was removed by design; the agent relies on BigQuery context and frontend history.

- `services/metrics_generator.py`, `services/devils_advocate.py`, `services/comparison_analysis.py`:
  - Specialized endpoints and agents for generating metrics and analyses. See each file for usage and examples.

---

## Environment variables

Create a `.env` in the project root (or export variables in your shell). Important variables:

- `GOOGLE_APPLICATION_CREDENTIALS` - path to service account JSON (optional if using ADC)
- `GOOGLE_CREDENTIALS_JSON` - (optional) raw JSON contents for fileless credentials helper
- `BQ_TABLE_ID` - BigQuery table id for the main dataset (e.g. `project.dataset.table`)
- `BQ_TABLE_STARTUP_PITCH_ID` - BigQuery table id for startup pitch table
- `GOOGLE_GENAI_MODEL` - LLM model name (default: `gemini-2.5-flash`)
- `LANGSMITH_API_KEY` / `LANGSMITH_URL` - (optional) LangSmith settings for tracing
- `AUTO_OPEN_SWAGGER` - set to `false` to disable auto-opening the browser on startup

Example `.env` snippet:

```
BQ_TABLE_ID=hackmind-471716.hackmind.deal_data
BQ_TABLE_STARTUP_PITCH_ID=hackmind-471716.hackmind.startup_pitch_data
GOOGLE_GENAI_MODEL=gemini-2.5-flash
AUTO_OPEN_SWAGGER=true
```

Notes on credentials:
- Development: run `gcloud auth application-default login` to enable Application Default Credentials (ADC).
- Fileless option: export a `GOOGLE_CREDENTIALS_JSON` env var containing the service account JSON and use the helper (noting this repo includes helper doc/comments but you can ask me to add a small function to load it at runtime).

---

## Local setup & testing

1) (Optional) Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

2) Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
# If requirements is missing packages, also consider:
# pip install google-cloud-bigquery python-dotenv langchain-google-genai langchain-core langchain requests uvicorn
```

3) Ensure credentials are available in the same shell you will run the server from:

Option A (ADC):

```bash
gcloud auth application-default login
```

Option B (.env):

```bash
set -o allexport; source .env; set +o allexport
```

Option C (fileless service account JSON):

```bash
export GOOGLE_CREDENTIALS_JSON="$(cat /path/to/key.json | jq -c .)"
# I can add a helper that writes this to a temp file and sets GOOGLE_APPLICATION_CREDENTIALS at runtime.
```

4) Run the server

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

5) Open API docs

Visit: `http://127.0.0.1:8000/docs` (Swagger UI). The app may auto-open this in your browser depending on `AUTO_OPEN_SWAGGER`.

6) Test `/chat` with structured history (example)

```bash
curl -s -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message":"Summarize growth potential and risks for this startup",
    "query_type":"default",
    "startup_id":"startup-123",
    "history":[
      {"role":"user","text":"Tell me about revenue trends."},
      {"role":"assistant","text":"Revenue has grown 20% QoQ."},
      {"role":"user","text":"Now summarize competitive risks."}
    ]
  }' | jq
```

Or run a quick local smoke test:

```bash
python - <<'PY'
import asyncio
from dotenv import load_dotenv
load_dotenv()
from services.chat_agent import run_chat_agent
res = asyncio.run(run_chat_agent("Summarize growth potential", history=[{"role":"user","text":"prior Q"}], startup_id=None))
print(res)
PY
```

---

## API endpoints (summary)

- `POST /chat` — Chat agent. Body: `message`, optional `query_type`, optional `startup_id`, optional `history: List[ChatMessage]`.
- `POST /analyze` — Metrics generation endpoint.
- `POST /getDevilsAdvocate` — Devil's advocate analysis.
- `POST /getComparisonData` — Competitor / market comparison.
- `POST /test-event` — GCS event processing.

Refer to Swagger UI for request/response schemas and examples.

---

## Structured chat history (recommended)

Use structured history so the agent can differentiate user vs assistant turns. This repo's `models/chat.py` defines:

- `ChatMessage`: `{ role: 'user' | 'assistant', text: string }`

Why structured history?
- Role separation improves context understanding and reduces hallucinations.
- Allows the agent to give follow-ups or correct prior assistant messages.

---

## Submodule: `specs`

This repository contains a Git submodule at `specs/` referenced in `.gitmodules`:

```
[submodule "specs"]
	path = specs
	url = https://github.com/HackMind-GenAI/copilot-startUp-specs.git
```

To initialize or update the submodule:

```bash
git submodule init
git submodule update --remote --recursive
```

---

## Troubleshooting

- Xcode license prompt (macOS): If `python` or dev tools fail with an Xcode license message, run `sudo xcodebuild -license` and accept.
- BigQuery credential errors: ensure ADC or service account is available in the same shell as uvicorn.
- LLM errors: verify `GOOGLE_GENAI_MODEL` and model access in your Google account.

If you'd like, I can:
- Add a small helper to load `GOOGLE_CREDENTIALS_JSON` into a temp file and set `GOOGLE_APPLICATION_CREDENTIALS` at runtime.
- Validate `history` in `main.py` to return helpful 400 errors for invalid formats.

---

If you want me to commit these README changes and/or add the optional helpers/validations, tell me which next step to take.
# copilot-startUp-backend

A FastAPI-based backend service for startup analysis and consultation, featuring AI-powered metrics generation and critical analysis capabilities.

## Features

- **Startup Analysis** (`/analyze`): Generate metrics and evaluation criteria for startup investments
- **Devil's Advocate Analysis** (`/getDevilsAdvocate`): Get critical analysis, risk assessment, and alternative perspectives using LangChain Google AI agents
- **Competitor Analysis** (`/getComparisonData`): Comprehensive market research and competitor analysis with web search capabilities using LangChain agents
- **GCS Event Handling** (`/test-event`): Process Google Cloud Storage events for file analysis

## API Endpoints

### POST /analyze
Analyze startup ideas and generate investment metrics.
```json
{
  "name": "Your startup description"
}
```

### POST /getDevilsAdvocate
Get comprehensive Devil's Advocate analysis using LangChain agents.
```json
{
  "message": "The idea or statement to analyze",
  "startup_idea": "Optional context about your startup"
}
```

**Response:**
```json
{
  "counter_argument": "Critical counter-arguments to the idea",
  "risk_assessment": "Detailed risk analysis and challenges", 
  "alternative_perspective": "Alternative viewpoints and approaches"
}
```

### POST /getComparisonData
Get comprehensive competitor analysis and market research using LangChain agents with web search capabilities.
```json
{
  "company_name": "Your company name",
  "industry": "Your industry sector",
  "business_model": "Optional business model description",
  "location": "Optional company location", 
  "target_market": "Optional target market description"
}
```

**Response:**
```json
{
  "industry_overview": "Comprehensive industry analysis and market insights",
  "market_size": "Market size estimates and growth projections",
  "key_competitors": [
    {
      "name": "Competitor name",
      "valuation": "Valuation information",
      "revenue": "Revenue details",
      "profitability_status": "Profitability analysis",
      "funding_rounds": "Funding history",
      "key_metrics": "Performance metrics",
      "competitive_advantages": "Competitive positioning"
    }
  ],
  "market_trends": "Key market trends and growth drivers",
  "investment_landscape": "Funding patterns and investor insights",
  "benchmarking_insights": "Detailed competitor analysis",
  "recommendations": "Strategic recommendations for investors"
}
```

### POST /test-event
Handle Google Cloud Storage events for document processing.

## Project Structure

```
copilot-startUp-backend/
├── main.py                     # FastAPI application
├── models/
│   └── summarize.py           # Pydantic models for request/response
├── services/
│   ├── metrics_generator.py   # Business logic and AI integration
│   ├── devils_advocate.py     # LangChain agent for critical analysis
│   └── comparison_analysis.py # LangChain agent for competitor research
├── requirements.txt            # Python dependencies
├── Dockerfile                 # Container configuration
└── README.md                 # This file
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
- Google AI API key for LangChain
- Google Cloud credentials (optional, for GCS features)

3. Run the server:
```bash
uvicorn main:app --reload --port 8000
```

4. View API documentation at `http://localhost:8000/docs`

## Services

- **metrics_generator.py**: Core startup analysis using Google Generative AI
- **devils_advocate.py**: Critical analysis service using LangChain agents with multiple tools for comprehensive risk evaluation
- **comparison_analysis.py**: Competitor research service using LangChain agents with web search capabilities and intelligent fallback

## Technologies

- FastAPI - Web framework
- LangChain with Google Generative AI - Core AI functionality
- LangChain Community - Web search and additional tools
- DuckDuckGo Search - Real-time web search capabilities
- Pydantic - Data validation and serialization
- Google Cloud Storage (optional) - File processing
- LangSmith - Agent tracing and debugging